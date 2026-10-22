# llm_factory.py — Cliente LLM con rotación de API keys y reintentos por cuota (429)
import threading
import time

from langchain_google_genai import ChatGoogleGenerativeAI

from src.config.settings import settings

_QUOTA_MARKERS = (
    "429",
    "resource_exhausted",
    "resourceexhausted",
    "quota",
    "rate limit",
    "503",
    "unavailable",
    "overloaded",
    "high demand",
    "403",
    "400",
    "permission",
    "permission denied",
    "permission_denied",
    "permissiondenied",
    "denied",
    "unauthenticated",
    "forbidden",
    "not_found",
    "not found",
    "invalid_argument",
    "invalid argument",
    "api key not valid",
    "api_key_not_valid",
    "project",
    "googleapierror",
    "googleapicallerror",
)


def build_llm(api_key: str | None = None) -> ChatGoogleGenerativeAI:
    """Construye el cliente Gemini con la siguiente llave del pool (rotación).
    max_retries=1 desactiva el backoff interno de langchain (6 reintentos ≈ 38 s
    por 429): el reintento lo hace LLMRouter rotando de llave al instante."""
    return ChatGoogleGenerativeAI(
        model=settings.LLM_MODEL,
        temperature=settings.LLM_TEMPERATURE,
        google_api_key=api_key or settings.get_next_api_key(),
        max_retries=1,
    )


def is_quota_error(exc: Exception) -> bool:
    """True si el error justifica ROTAR de API key: cuota (429) o fallo de
    auth/proyecto de una llave específica (403/400/not_found/invalid_argument/
    GoogleAPICallError/PermissionDenied...).
    El 404 de modelo (GoogleModelNotFoundError) NO rota: todas las llaves
    fallarían igual, es un problema del ID del modelo, no de la llave."""
    text = f"{type(exc).__name__}: {exc}".lower()
    if (
        "modelnotfound" in text
        or "model not found" in text
        or "no longer available" in text
    ):
        return False
    if "function call turn comes" in text:
        return False
    return any(marker in text for marker in _QUOTA_MARKERS)


class LLMRouter:
    """Cliente hilo-seguro: invoca con reintentos rotando llaves del pool ante 429.

    Intento 1 usa la llave actual del ciclo; cada rotación avanza el pool y
    re-bindea las tools al nuevo cliente. Agota `LLM_MAX_RETRIES` (== tamaño
    del pool) antes de re-lanzar la excepción.
    """

    def __init__(self, tools: list):
        self._tools = tools
        self._lock = threading.Lock()
        self._bound = build_llm().bind_tools(tools)

    @property
    def bound(self):
        return self._bound

    def _rotate(self) -> None:
        with self._lock:
            # build_llm() avanza itertools.cycle al siguiente pool de llaves
            self._bound = build_llm().bind_tools(self._tools)

    def invoke(self, messages):
        attempts = settings.LLM_MAX_RETRIES
        for attempt in range(1, attempts + 1):
            t0 = time.time()
            try:
                return self._bound.invoke(messages)
            except Exception as e:
                dt = time.time() - t0
                print(
                    f"DEBUG ERROR intento {attempt}/{attempts} ({dt:.1f}s): "
                    f"{type(e).__name__} - {e}",
                    flush=True,
                )
                if not is_quota_error(e) or attempt == attempts:
                    raise
                self._rotate()
