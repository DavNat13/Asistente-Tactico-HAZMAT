"""Persistencia de telemetría y auditoría en MongoDB (agent_runs, security_events).

- Escrituras en hilo aparte: la telemetría nunca suma latencia ni rompe una respuesta.
- Usuarios SEUDONIMIZADOS (sha256 con sal): el dashboard nunca muestra identidades.
- TTL (TELEMETRY_TTL_DAYS) → retención limitada de datos (minimización, Ley 21.719).
"""

from __future__ import annotations

import hashlib
import logging
import threading
from datetime import UTC, datetime

from src.config.settings import settings

log = logging.getLogger("hazmat.telemetry")

RUNS_COLLECTION = "agent_runs"
SECURITY_COLLECTION = "security_events"

_db_lock = threading.Lock()
_db = None
_indexes_ready = False


def pseudonymize(value: str | None) -> str | None:
    if not value:
        return None
    return hashlib.sha256(f"{settings.TELEMETRY_SALT}:{value}".encode()).hexdigest()[
        :16
    ]


def get_db():
    global _db, _indexes_ready
    with _db_lock:
        if _db is None:
            from pymongo import MongoClient

            client = MongoClient(
                settings.MONGODB_URI,
                serverSelectionTimeoutMS=settings.MONGODB_TIMEOUT_MS,
            )
            _db = client[settings.MONGODB_DB_NAME]
        if not _indexes_ready:
            ttl = settings.TELEMETRY_TTL_DAYS * 86400
            try:
                _db[RUNS_COLLECTION].create_index(
                    "created_at", expireAfterSeconds=ttl, name="ttl_runs"
                )
                _db[RUNS_COLLECTION].create_index("run_id", unique=True, name="run_id")
                _db[SECURITY_COLLECTION].create_index(
                    "created_at", expireAfterSeconds=ttl, name="ttl_sec"
                )
                _indexes_ready = True
            except Exception as e:  # noqa: BLE001
                log.warning("No se pudieron crear índices de telemetría: %s", e)
    return _db


def run_async(fn, *args) -> None:
    threading.Thread(target=fn, args=args, daemon=True).start()


def save_run(doc: dict, sync: bool = False) -> None:
    def _write(d):
        try:
            get_db()[RUNS_COLLECTION].insert_one(d)
        except Exception as e:  # noqa: BLE001
            log.warning("No se pudo guardar telemetría: %s", e)

    _write(doc) if sync else run_async(_write, doc)


def record_feedback(run_id: str, value: int, user_id: str | None = None) -> None:
    """value: 1 (útil) / -1 (no útil). Solo el dueño de la ejecución puede calificarla."""

    def _write():
        try:
            get_db()[RUNS_COLLECTION].update_one(
                {"run_id": run_id, "user": pseudonymize(user_id)},
                {"$set": {"feedback": int(value), "feedback_at": datetime.now(UTC)}},
            )
        except Exception as e:  # noqa: BLE001
            log.warning("No se pudo guardar feedback: %s", e)

    run_async(_write)


def security_event(
    kind: str, *, user_id: str | None = None, detail: str = "", severity: str = "medium"
) -> None:
    """Auditoría de seguridad (bloqueos, login fallido, rate limit). Nunca guarda el texto del usuario."""
    doc = {
        "created_at": datetime.now(UTC),
        "kind": kind,
        "severity": severity,
        "user": pseudonymize(user_id),
        "detail": detail[:200],
    }
    log.warning("security_event %s %s", kind, detail[:80])

    def _write(d):
        try:
            get_db()[SECURITY_COLLECTION].insert_one(d)
        except Exception as e:  # noqa: BLE001
            log.warning("No se pudo guardar evento de seguridad: %s", e)

    run_async(_write, doc)


def classify_error(exc: BaseException) -> str:
    text = f"{type(exc).__name__}: {exc}".lower()
    rules = (  # el orden importa: "ServerSelectionTimeoutError" es de base de datos
        (("serverselection", "mongo", "getaddrinfo", "autoreconnect"), "database"),
        (("429", "resource_exhausted", "quota"), "quota"),
        (("503", "unavailable", "overloaded", "high demand"), "llm_unavailable"),
        (("timeout", "timed out", "deadline"), "timeout"),
        (("recursion",), "recursion_limit"),
        (("api key", "permission", "403"), "auth"),
    )
    for markers, label in rules:
        if any(m in text for m in markers):
            return label
    return type(exc).__name__
