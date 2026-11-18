"""Autenticación de usuarios.

- Inicio de sesión con nombre de usuario o correo.
- Bloqueo temporal tras LOGIN_MAX_ATTEMPTS intentos fallidos (aviso por correo al titular).
- Mensaje genérico ante cualquier rechazo (no revela si la cuenta existe) y tiempo similar
  en ambos casos (mitiga enumeración por timing). Cada evento queda en `security_events`.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from src.config.settings import settings
from src.observability.store import security_event
from src.security.accounts import (  # noqa: F401 — API pública reexportada
    ROLES,
    USERS,
    _users,
    create_user,
    find_by_login,
)
from src.security.passwords import (  # noqa: F401 — API pública reexportada
    MIN_PASSWORD,
    hash_password,
    validate_password,
    verify_password,
)


def _public(user: dict) -> dict:
    return {
        "username": user["_id"],
        "name": user.get("name", user["_id"]),
        "role": user.get("role", "operador"),
        "email": user.get("email"),
    }


def _lock(user: dict, attempts: int, now: datetime) -> dict:
    security_event(
        "account_locked",
        user_id=user["_id"],
        detail=f"{attempts} intentos",
        severity="high",
    )
    if user.get("email"):
        from src.notify.notifications import notify_account_locked

        notify_account_locked(user)
    return {
        "failed_attempts": 0,
        "locked_until": now + timedelta(minutes=settings.LOGIN_LOCK_MINUTES),
    }


def authenticate(login: str, password: str) -> dict | None:
    """Devuelve {"username", "name", "role", "email"} o None."""
    user = find_by_login(login)
    now = datetime.now(UTC)
    if not user:
        hash_password(password)  # tiempo similar al caso válido
        security_event(
            "login_failed",
            user_id=login[:32],
            detail="cuenta inexistente",
            severity="low",
        )
        return None
    locked = user.get("locked_until")
    if locked and locked.replace(tzinfo=UTC) > now:
        security_event("login_locked", user_id=user["_id"], detail="cuenta bloqueada")
        return None
    if not verify_password(password, user["password_hash"]):
        attempts = user.get("failed_attempts", 0) + 1
        update: dict = {"failed_attempts": attempts}
        if attempts >= settings.LOGIN_MAX_ATTEMPTS:
            update = _lock(user, attempts, now)
        _users().update_one({"_id": user["_id"]}, {"$set": update})
        security_event(
            "login_failed",
            user_id=user["_id"],
            detail=f"intento {attempts}",
            severity="low",
        )
        return None
    _users().update_one(
        {"_id": user["_id"]},
        {"$set": {"failed_attempts": 0, "locked_until": None, "last_login": now}},
    )
    return _public(user)
