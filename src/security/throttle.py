"""Límites anti-abuso por clave (correo, IP o cuenta) con ventana fija, compartidos vía MongoDB.

- La clave se seudonimiza (sha256 con sal): nunca se guarda el correo ni la IP en claro.
- Colección `rate_limits` con TTL sobre `expires_at` (los contadores se borran solos).
- Si Mongo no responde, cae a un contador en memoria del proceso.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict
from datetime import UTC, datetime

from src.observability.store import get_db, pseudonymize, security_event

_COLLECTION = "rate_limits"
_local: dict[str, int] = defaultdict(int)
_lock = threading.Lock()
_index_ready = False


def _hit(key: str, window_s: int) -> int:
    global _index_ready
    start = int(time.time()) // window_s * window_s
    doc_id = f"{key}:{start}"
    try:
        col = get_db()[_COLLECTION]
        if not _index_ready:
            col.create_index("expires_at", expireAfterSeconds=0, name="ttl_rate")
            _index_ready = True
        expires = datetime.fromtimestamp(start + 2 * window_s, UTC)
        doc = col.find_one_and_update(
            {"_id": doc_id},
            {"$inc": {"count": 1}, "$setOnInsert": {"expires_at": expires}},
            upsert=True,
            return_document=True,
        )
        return int(doc["count"])
    except Exception:  # noqa: BLE001 — degradar a memoria local
        with _lock:
            if len(_local) > 5000:
                _local.clear()
            _local[doc_id] += 1
            return _local[doc_id]


def allow(scope: str, value: str | None, limit: int, window_s: int = 3600) -> bool:
    """True si la acción está permitida. Sin valor (p. ej. IP desconocida) no se limita."""
    if not value or limit <= 0:
        return True
    key = f"{scope}:{pseudonymize(value.strip().lower())}"
    if _hit(key, window_s) <= limit:
        return True
    security_event(
        "throttled", detail=f"{scope} > {limit}/{window_s}s", severity="medium"
    )
    return False


def reset_local() -> None:
    with _lock:
        _local.clear()
