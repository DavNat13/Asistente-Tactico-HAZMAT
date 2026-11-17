"""Autenticación de usuarios (colección `users` en MongoDB).

- Contraseñas con scrypt (función de derivación resistente a fuerza bruta por GPU, stdlib) + sal única.
- Comparación en tiempo constante (hmac.compare_digest).
- Bloqueo temporal tras LOGIN_MAX_ATTEMPTS intentos fallidos; mensaje genérico (no revela si el
  usuario existe). Cada evento queda en `security_events` con el usuario seudonimizado.
- Roles: `operador` (chat) y `admin` (chat + dashboard de observabilidad).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
from datetime import UTC, datetime, timedelta

from src.config.settings import settings
from src.observability.store import get_db, security_event
from src.session.sanitizer import InputSanitizer

USERS = "users"
ROLES = ("operador", "admin")
MIN_PASSWORD = 10
_N, _R, _P = 2**14, 8, 1


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.scrypt(password.encode(), salt=salt, n=_N, r=_R, p=_P, dklen=64)
    b64 = base64.b64encode
    return f"scrypt${_N}${_R}${_P}${b64(salt).decode()}${b64(dk).decode()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, n, r, p, salt, digest = stored.split("$")
        if algo != "scrypt":
            return False
        dk = hashlib.scrypt(
            password.encode(),
            salt=base64.b64decode(salt),
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=64,
        )
        return hmac.compare_digest(dk, base64.b64decode(digest))
    except (ValueError, TypeError):
        return False


def validate_password(password: str) -> None:
    if len(password) < MIN_PASSWORD:
        raise ValueError(f"La contraseña debe tener al menos {MIN_PASSWORD} caracteres")
    if password.isalpha() or password.isdigit():
        raise ValueError("La contraseña debe combinar letras y números o símbolos")


def create_user(
    username: str, password: str, role: str = "operador", name: str = ""
) -> dict:
    username = InputSanitizer.sanitize_username(username)
    if role not in ROLES:
        raise ValueError(f"Rol inválido: {role}")
    validate_password(password)
    doc = {
        "_id": username,
        "name": InputSanitizer.sanitize_title(name or username),
        "role": role,
        "password_hash": hash_password(password),
        "created_at": datetime.now(UTC),
        "failed_attempts": 0,
        "locked_until": None,
        "active": True,
    }
    get_db()[USERS].replace_one({"_id": username}, doc, upsert=True)
    return {k: doc[k] for k in ("_id", "name", "role")}


def authenticate(username: str, password: str) -> dict | None:
    """Devuelve {"username", "name", "role"} o None. Nunca indica la causa exacta del rechazo."""
    try:
        username = InputSanitizer.sanitize_username(username)
    except ValueError:
        return None
    users = get_db()[USERS]
    user = users.find_one({"_id": username, "active": True})
    now = datetime.now(UTC)
    if not user:
        hash_password(
            password
        )  # tiempo similar al caso válido (mitiga enumeración por timing)
        security_event(
            "login_failed",
            user_id=username,
            detail="usuario inexistente",
            severity="low",
        )
        return None
    locked = user.get("locked_until")
    if locked and locked.replace(tzinfo=UTC) > now:
        security_event("login_locked", user_id=username, detail="cuenta bloqueada")
        return None
    if not verify_password(password, user["password_hash"]):
        attempts = user.get("failed_attempts", 0) + 1
        update: dict = {"failed_attempts": attempts}
        if attempts >= settings.LOGIN_MAX_ATTEMPTS:
            update.update(
                failed_attempts=0,
                locked_until=now + timedelta(minutes=settings.LOGIN_LOCK_MINUTES),
            )
            security_event(
                "account_locked",
                user_id=username,
                detail=f"{attempts} intentos",
                severity="high",
            )
        users.update_one({"_id": username}, {"$set": update})
        security_event(
            "login_failed",
            user_id=username,
            detail=f"intento {attempts}",
            severity="low",
        )
        return None
    users.update_one(
        {"_id": username},
        {"$set": {"failed_attempts": 0, "locked_until": None, "last_login": now}},
    )
    return {
        "username": username,
        "name": user.get("name", username),
        "role": user.get("role", "operador"),
    }
