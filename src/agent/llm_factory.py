"""Cliente Gemini resiliente: rotación de API keys + cadena de modelos de respaldo + telemetría.

- Error de llave (429/403)          → siguiente API key del pool.
- Error de modelo (503/timeout/404) → siguiente modelo de LLM_FALLBACK_MODELS. El modelo caído queda
  "abierto" (circuit breaker) por MODEL_COOLDOWN_S antes de volver a probarlo.
- Otro error (400, bug)             → se relanza sin reintentos.
"""

from __future__ import annotations

import logging
import threading
import time

from langchain_google_genai import ChatGoogleGenerativeAI

from src.agent.llm_utils import content_text, failure_kind
from src.config.settings import settings
from src.observability.telemetry import current

log = logging.getLogger("hazmat.llm")

_down_until: dict[
    str, float
] = {}  # modelo -> timestamp hasta el que se considera caído
_down_lock = threading.Lock()


def model_chain(first: str | None = None) -> list[str]:
    chain = [settings.LLM_MODEL, *settings.LLM_FALLBACK_MODELS]
    if first:  # p. ej. el clasificador de guardrails prefiere el modelo liviano
        chain = [first, *[m for m in chain if m != first]]
    now = time.time()
    healthy = [m for m in chain if _down_until.get(m, 0) <= now]
    return healthy or chain


def _mark_down(model: str) -> None:
    with _down_lock:
        _down_until[model] = time.time() + settings.MODEL_COOLDOWN_S


def build_llm(
    model: str | None = None, temperature: float | None = None
) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=model or settings.LLM_MODEL,
        temperature=settings.LLM_TEMPERATURE if temperature is None else temperature,
        google_api_key=settings.get_next_api_key(),
        max_retries=0,  # los reintentos los gestiona LLMRouter
        timeout=settings.LLM_TIMEOUT_S,
    )


def _record(response, model: str) -> None:
    rec = current()
    if rec is not None:
        rec.llm(getattr(response, "usage_metadata", None))
        rec.set(model=model)


class LLMRouter:
    """Invoca el LLM con reintentos dirigidos según la causa del error (hilo-seguro)."""

    def __init__(self, tools: list | None = None):
        self._tools = tools or []

    def _client(self, model: str, with_tools: bool, temperature: float | None):
        llm = build_llm(model, temperature)
        return llm.bind_tools(self._tools) if (with_tools and self._tools) else llm

    def invoke(
        self,
        messages,
        *,
        with_tools: bool = True,
        temperature: float | None = None,
        prefer: str | None = None,
    ):
        models = model_chain(prefer)
        max_attempts = settings.LLM_MAX_RETRIES + len(models)
        idx, attempt = 0, 0
        while attempt < max_attempts:
            attempt += 1
            model = models[idx]
            t0 = time.perf_counter()
            try:
                response = self._client(model, with_tools, temperature).invoke(messages)
                _record(response, model)
                return response
            except Exception as e:
                kind = failure_kind(e)
                log.warning(
                    "LLM %s intento %d falló en %.1fs (%s): %s",
                    model,
                    attempt,
                    time.perf_counter() - t0,
                    kind,
                    type(e).__name__,
                )
                rec = current()
                if kind is None or attempt >= max_attempts:
                    raise
                if kind == "model":
                    _mark_down(model)
                    if idx + 1 >= len(models):
                        raise
                    idx += 1
                    if rec is not None:
                        rec.set(model_fallback=True)
                elif rec is not None:  # "key": build_llm toma la siguiente llave
                    rec.rotation()
        raise RuntimeError("LLM sin intentos disponibles")


_plain_router = LLMRouter()


def invoke_plain(
    messages, temperature: float | None = None, prefer: str | None = None
) -> str:
    """Llamada simple sin herramientas (clasificador de guardrails, juez de evals)."""
    response = _plain_router.invoke(
        messages, with_tools=False, temperature=temperature, prefer=prefer
    )
    return content_text(response.content)
