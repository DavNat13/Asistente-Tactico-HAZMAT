"""Telemetría por ejecución del agente (EV3 — IE1/IE2/IE3).

Cada consulta crea un `RunRecorder` (accesible vía contextvar con `current()`) que acumula:
latencia total / TTFT / por nodo, herramientas usadas, tokens, llamadas LLM, rotaciones de API key,
guardrails, grounding de citas, recursos (CPU s, RSS MB) y error tipificado.
"""

from __future__ import annotations

import contextvars
import logging
import time
import uuid
from datetime import UTC, datetime

import psutil

from src.config.settings import settings
from src.observability.store import classify_error, pseudonymize, save_run

log = logging.getLogger("hazmat.telemetry")

AGENT_VERSION = "5.0.0"

_current: contextvars.ContextVar[RunRecorder | None] = contextvars.ContextVar(
    "hazmat_run", default=None
)
_process = psutil.Process()


class RunRecorder:
    def __init__(
        self,
        *,
        user_id: str | None,
        thread_id: str | None,
        query: str,
        channel: str = "ui",
    ):
        self.run_id = str(uuid.uuid4())
        self._t0 = time.perf_counter()
        self._cpu0 = _process.cpu_times()
        self._token = None
        self.doc: dict = {
            "run_id": self.run_id,
            "created_at": datetime.now(UTC),
            "agent_version": AGENT_VERSION,
            "model": settings.LLM_MODEL,
            "embedding_model": settings.EMBEDDING_MODEL,
            "channel": channel,
            "user": pseudonymize(user_id),
            "thread": pseudonymize(thread_id),
            "query_chars": len(query or ""),
            "complexity": None,
            "nodes": [],
            "tools": [],
            "llm_calls": 0,
            "tokens_in": 0,
            "tokens_out": 0,
            "key_rotations": 0,
            "n_chunks": 0,
            "top_score": None,
            "blocked": False,
            "block_reason": None,
            "guard_layer": None,
            "pii_redacted": 0,
            "output_issues": [],
            "grounded": None,
            "citations": 0,
            "status": "ok",
            "error_type": None,
            "ttft_ms": None,
            "latency_ms": None,
            "feedback": None,
        }

    def __enter__(self):
        self._token = _current.set(self)
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc is not None:
            self.error(exc)
        self.finish()
        if self._token is not None:
            _current.reset(self._token)
        return False

    def set(self, **fields) -> None:
        self.doc.update(fields)

    def node(self, name: str, ms: float) -> None:
        self.doc["nodes"].append({"node": name, "ms": round(ms, 1)})

    def tool(self, name: str, ms: float, n_docs: int) -> None:
        self.doc["tools"].append({"tool": name, "ms": round(ms, 1), "n_docs": n_docs})

    def llm(self, usage: dict | None) -> None:
        usage = usage or {}
        self.doc["llm_calls"] += 1
        self.doc["tokens_in"] += int(usage.get("input_tokens", 0) or 0)
        self.doc["tokens_out"] += int(usage.get("output_tokens", 0) or 0)

    def rotation(self) -> None:
        self.doc["key_rotations"] += 1

    def first_token(self) -> None:
        if self.doc["ttft_ms"] is None:
            self.doc["ttft_ms"] = round((time.perf_counter() - self._t0) * 1000, 1)

    def error(self, exc: BaseException) -> None:
        self.doc["status"] = "error"
        self.doc["error_type"] = classify_error(exc)

    def finish(self) -> None:
        if self.doc["latency_ms"] is not None:
            return
        self.doc["latency_ms"] = round((time.perf_counter() - self._t0) * 1000, 1)
        cpu1 = _process.cpu_times()
        self.doc["cpu_s"] = round(
            (cpu1.user - self._cpu0.user) + (cpu1.system - self._cpu0.system), 3
        )
        self.doc["rss_mb"] = round(_process.memory_info().rss / 1_048_576, 1)
        if self.doc["status"] == "ok" and self.doc["blocked"]:
            self.doc["status"] = "blocked"
        d = self.doc
        log.info(
            "run=%s complexity=%s status=%s latency_ms=%s tools=%d tokens=%d/%d",
            self.run_id[:8],
            d["complexity"],
            d["status"],
            d["latency_ms"],
            len(d["tools"]),
            d["tokens_in"],
            d["tokens_out"],
        )

    def save(self, sync: bool = False) -> None:
        self.finish()
        save_run(dict(self.doc), sync=sync)


def current() -> RunRecorder | None:
    return _current.get()
