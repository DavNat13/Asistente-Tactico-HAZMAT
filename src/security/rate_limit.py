"""Rate limiting por usuario (ventana fija de 1 minuto).

Protege la cuota del LLM y mitiga abuso / denegación de servicio (OWASP LLM10 — consumo no acotado).
Usa MongoDB (colección con TTL) para que el límite se comparta entre réplicas; si Mongo no responde,
cae a un contador en memoria del proceso.
"""

from __future__ import annotations

import threading
from collections import defaultdict
from datetime import UTC, datetime, timedelta

from src.config.settings import settings
from src.observability.store import get_db, pseudonymize, security_event

_COLLECTION = "rate_limits"
_local: dict[str, int] = defaultdict(int)
_lock = threading.Lock()
_index_ready = False


def _window_key(user_id: str) -> tuple[str, datetime]:
    now = datetime.now(UTC).replace(second=0, microsecond=0)
    return f"{pseudonymize(user_id)}:{now.isoformat()}", now


def _mongo_hit(key: str, window: datetime) -> int:
    global _index_ready
    col = get_db()[_COLLECTION]
    if not _index_ready:
        col.create_index("expires_at", expireAfterSeconds=0, name="ttl_rate")
        _index_ready = True
    doc = col.find_one_and_update(
        {"_id": key},
        {
            "$inc": {"count": 1},
            "$setOnInsert": {"expires_at": window + timedelta(minutes=2)},
        },
        upsert=True,
        return_document=True,
    )
    return int(doc["count"])


def check_rate_limit(user_id: str | None, limit: int | None = None) -> bool:
    """True si la consulta está permitida."""
    limit = limit or settings.RATE_LIMIT_PER_MIN
    if not user_id or limit <= 0:
        return True
    key, window = _window_key(user_id)
    try:
        count = _mongo_hit(key, window)
    except Exception:  # noqa: BLE001 — degradar a memoria local
        with _lock:
            _local[key] += 1
            count = _local[key]
            if len(_local) > 5000:
                _local.clear()
    if count > limit:
        security_event(
            "rate_limit",
            user_id=user_id,
            detail=f"{count}/{limit} por minuto",
            severity="low",
        )
        return False
    return True


def reset_local() -> None:
    with _lock:
        _local.clear()
