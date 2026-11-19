"""Códigos de un solo uso (6 dígitos) para verificar el correo y restablecer la contraseña.

- Se generan con `secrets` y se guarda SOLO su HMAC-SHA256 (clave `OTP_SECRET`).
- Comparación en tiempo constante (`hmac.compare_digest`) y uso único atómico.
- Un código activo por cuenta y propósito en `email_tokens` (TTL sobre `expires_at`).
- Expiran en 15 min (signup) o 10 min (reset); al 5.º intento fallido el código queda invalidado.
- El código en claro solo existe en memoria para enviarlo por correo: nunca se registra.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import math
import secrets
from datetime import UTC, datetime, timedelta

from src.config.settings import settings
from src.observability.store import get_db, security_event

log = logging.getLogger("hazmat.otp")
TOKENS = "email_tokens"
TTL_MINUTES = {"signup": 15, "reset": 10}
MAX_ATTEMPTS = 5
RESEND_COOLDOWN_S = 60
_process_key = secrets.token_bytes(32)
_index_ready = False


def _key() -> bytes:
    if settings.OTP_SECRET:
        return settings.OTP_SECRET.encode()
    return _process_key  # sin OTP_SECRET: los códigos solo valen en este proceso


def generate_code() -> str:
    return f"{secrets.randbelow(10**6):06d}"


def hash_code(code: str, user_id: str, purpose: str) -> str:
    msg = f"{purpose}:{user_id}:{code}".encode()
    return hmac.new(_key(), msg, hashlib.sha256).hexdigest()


def _tokens():
    global _index_ready
    col = get_db()[TOKENS]
    if not _index_ready:
        try:
            col.create_index("expires_at", expireAfterSeconds=0, name="ttl_tokens")
            col.create_index("user_id", name="token_user")
            _index_ready = True
        except Exception as e:  # noqa: BLE001
            log.debug("Índices de códigos no creados: %s", e)
    return col


def _id(user_id: str, purpose: str) -> str:
    return f"{purpose}:{user_id}"


def _aware(dt: datetime) -> datetime:
    return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt


def issue(user_id: str, purpose: str) -> str:
    """Crea (o reemplaza) el código activo. Devuelve el código en claro SOLO para enviarlo."""
    if purpose not in TTL_MINUTES:
        raise ValueError(f"Propósito inválido: {purpose}")
    code, now = generate_code(), datetime.now(UTC)
    doc = {
        "_id": _id(user_id, purpose),
        "user_id": user_id,
        "purpose": purpose,
        "code_hash": hash_code(code, user_id, purpose),
        "created_at": now,
        "expires_at": now + timedelta(minutes=TTL_MINUTES[purpose]),
        "attempts": 0,
        "last_sent_at": now,
        "used_at": None,
    }
    _tokens().replace_one({"_id": doc["_id"]}, doc, upsert=True)
    return code


def _live(doc: dict | None) -> bool:
    return bool(
        doc
        and doc.get("used_at") is None
        and doc.get("attempts", 0) < MAX_ATTEMPTS
        and _aware(doc["expires_at"]) > datetime.now(UTC)
    )


def active(user_id: str, purpose: str) -> bool:
    return _live(_tokens().find_one({"_id": _id(user_id, purpose)}))


def cooldown_left(user_id: str, purpose: str) -> int:
    """Segundos que faltan para poder reenviar un código (0 si ya se puede)."""
    doc = _tokens().find_one({"_id": _id(user_id, purpose)})
    if not doc or not doc.get("last_sent_at"):
        return 0
    elapsed = (datetime.now(UTC) - _aware(doc["last_sent_at"])).total_seconds()
    return max(0, math.ceil(RESEND_COOLDOWN_S - elapsed))


def _failed(user_id: str, detail: str) -> None:
    security_event("otp_failed", user_id=user_id, detail=detail, severity="low")


def verify(user_id: str, purpose: str, code: str) -> bool:
    """True si el código es correcto, vigente y no usado; lo consume. Nunca registra el código."""
    code = (code or "").strip()
    expected = hash_code(code, user_id, purpose)  # siempre se calcula: tiempo similar
    doc = _tokens().find_one({"_id": _id(user_id, purpose)})
    now = datetime.now(UTC)
    if not _live(doc):
        _failed(user_id, f"{purpose}: sin código vigente")
        return False
    if hmac.compare_digest(expected, doc["code_hash"]) and code.isdigit():
        claimed = _tokens().update_one(
            {"_id": doc["_id"], "used_at": None}, {"$set": {"used_at": now}}
        )
        return claimed.modified_count == 1  # uso único ante envíos simultáneos
    attempts = doc.get("attempts", 0) + 1
    update: dict = {"attempts": attempts}
    if attempts >= MAX_ATTEMPTS:
        update["used_at"] = now  # invalidado: hay que pedir un código nuevo
    _tokens().update_one({"_id": doc["_id"]}, {"$set": update})
    _failed(user_id, f"{purpose}: intento {attempts}")
    return False


def invalidate(user_id: str, purpose: str | None = None) -> None:
    """Marca como usados los códigos vigentes del usuario (todos o de un propósito)."""
    query: dict = {"user_id": user_id, "used_at": None}
    if purpose:
        query["purpose"] = purpose
    _tokens().update_many(query, {"$set": {"used_at": datetime.now(UTC)}})


def delete_for(user_id: str) -> None:
    _tokens().delete_many({"user_id": user_id})
