"""Punto de entrada único al agente (UI, evaluaciones y futuros canales).

Pipeline: rate limit → redacción de PII → grafo (guardrails, router, RAG, agente) → telemetría.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator

from src.agent.agent import agent_app
from src.agent.llm_factory import content_text
from src.agent.service_io import ERROR_MESSAGES, STATUS_LABELS, _inputs, _result
from src.config.settings import settings
from src.observability.store import classify_error
from src.observability.telemetry import RunRecorder
from src.security.patterns import REFUSALS
from src.security.rate_limit import check_rate_limit

log = logging.getLogger("hazmat.service")


def stream_query(
    query: str,
    *,
    thread_id: str | None = None,
    user_id: str | None = None,
    history: list[dict] | None = None,
    channel: str = "ui",
) -> Iterator[dict]:
    """Genera eventos: {"type": "status"|"token"|"final", ...}. El evento final trae la respuesta validada."""
    rec = RunRecorder(
        user_id=user_id, thread_id=thread_id, query=query, channel=channel
    )
    with rec:
        if channel != "eval" and not check_rate_limit(user_id):
            rec.set(blocked=True, block_reason="rate_limit", complexity="low")
            yield {
                "type": "final",
                **_result({"answer": REFUSALS["rate_limit"], "blocked": True}, rec),
            }
            rec.save()
            return
        inputs, n_pii = _inputs(query, history)
        rec.set(pii_redacted=n_pii)
        state: dict = dict(inputs)
        config = {
            "recursion_limit": settings.AGENT_RECURSION_LIMIT,
            "run_name": "hazmat_agent",
            "metadata": {"run_id": rec.run_id, "channel": channel},
        }
        try:
            for mode, payload in agent_app.stream(
                inputs, config=config, stream_mode=["updates", "messages"]
            ):
                if mode == "updates":
                    for node, update in (payload or {}).items():
                        state.update(
                            {
                                k: v
                                for k, v in (update or {}).items()
                                if k not in ("messages", "docs")
                            }
                        )
                        state["docs"] = state.get("docs", []) + (update or {}).get(
                            "docs", []
                        )
                        state["messages"] = state.get("messages", []) + (
                            update or {}
                        ).get("messages", [])
                        if node in STATUS_LABELS:
                            yield {
                                "type": "status",
                                "node": node,
                                "label": STATUS_LABELS[node],
                            }
                elif mode == "messages":
                    chunk, meta = payload
                    if meta.get("langgraph_node") != "agent" or getattr(
                        chunk, "tool_call_chunks", None
                    ):
                        continue
                    text = content_text(chunk.content)
                    if text:
                        rec.first_token()
                        yield {"type": "token", "text": text}
        except Exception as e:
            rec.error(e)
            log.error(
                "Fallo del agente run=%s tipo=%s", rec.run_id, rec.doc["error_type"]
            )
            log.debug("detalle", exc_info=True)
            state["answer"] = ERROR_MESSAGES.get(
                classify_error(e), "Ocurrió un error al procesar la consulta."
            )
        rec.finish()
        yield {"type": "final", **_result(state, rec)}
    rec.save(sync=channel == "eval")


def run_query(query: str, **kwargs) -> dict:
    """Versión síncrona (evaluaciones, tests): devuelve solo el evento final."""
    final: dict = {}
    for event in stream_query(query, **kwargs):
        if event["type"] == "final":
            final = event
    return final
