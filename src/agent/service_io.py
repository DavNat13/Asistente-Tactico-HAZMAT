"""Entradas/salidas del servicio del agente: historial, redacción de PII y formato del resultado."""

from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage

from src.config.settings import settings
from src.observability.telemetry import RunRecorder
from src.security.pii import redact

STATUS_LABELS = {
    "guard_in": "Validando la consulta…",
    "classify": "Clasificando complejidad…",
    "prefetch": "Buscando en la GRE 2024…",
    "agent": "Redactando respuesta…",
    "tools": "Consultando herramientas…",
    "guard_out": "Verificando citas…",
}

ERROR_MESSAGES = {
    "quota": "Se alcanzó el límite temporal de la API de IA. Espera un minuto e intenta de nuevo.",
    "database": "La base de conocimiento no está disponible en este momento. Intenta en unos minutos.",
    "timeout": "El servicio de IA tardó demasiado en responder. Intenta nuevamente.",
    "llm_unavailable": "El servicio de IA está saturado en este momento. Intenta en un minuto.",
}


def _history_messages(history: list[dict] | None) -> list:
    msgs = []
    for h in (history or [])[-settings.AGENT_HISTORY_MESSAGES :]:
        text, _ = redact(h.get("content", ""))
        if not text:
            continue
        msgs.append(
            HumanMessage(content=text)
            if h.get("role") == "user"
            else AIMessage(content=text[:2000])
        )
    return msgs


def _inputs(query: str, history: list[dict] | None) -> tuple[dict, int]:
    clean, n_pii = redact(query)
    return {
        "query": clean,
        "messages": [*_history_messages(history), HumanMessage(content=clean)],
    }, n_pii


def _result(state: dict, rec: RunRecorder) -> dict:
    tool_msgs = [
        m for m in state.get("messages", []) if getattr(m, "type", "") == "tool"
    ]
    return {
        "run_id": rec.run_id,
        "answer": state.get("answer", ""),
        "chunks": state.get("docs", []),
        "complexity": state.get("complexity"),
        "blocked": bool(state.get("blocked")),
        "tool_calls": len(tool_msgs),
        "tokens_in": rec.doc["tokens_in"],
        "tokens_out": rec.doc["tokens_out"],
        "grounding": state.get("grounding"),
        "latency_ms": rec.doc["latency_ms"],
    }
