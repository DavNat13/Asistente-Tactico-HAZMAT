"""Fallos del registro: nunca en silencio.

Ante un error inesperado se registra el traceback en el log del servidor (sin correo ni contraseña),
un evento `signup_failed` con la fase y una referencia corta, y se deshace la cuenta a medio crear.
El rollback tiene su propio try: si también falla, no oculta el error original.
"""

from __future__ import annotations

import logging
import uuid

from src.observability.store import get_db, security_event
from src.security import otp

log = logging.getLogger("hazmat.signup")
USERS = "users"


class SignupError(Exception):
    """Error inesperado del registro, con referencia para buscarlo en el log y en `security_events`."""

    def __init__(self, ref: str):
        self.ref = ref
        super().__init__(
            f"No se pudo crear la cuenta (ref. {ref}). "
            "Intenta de nuevo o avisa al administrador"
        )


def rollback(user_id: str | None, reason: str) -> None:
    """Elimina la cuenta NUEVA no verificada y sus códigos. Nunca lanza."""
    if not user_id:
        return
    try:
        get_db()[USERS].delete_one({"_id": user_id, "email_verified": False})
        otp.delete_for(user_id)
        security_event("signup_rolled_back", user_id=user_id, detail=reason)
    except Exception:
        log.exception("No se pudo deshacer el registro de una cuenta pendiente")


def failure(phase: str, exc: BaseException, user_id: str | None) -> SignupError:
    """Registra el error (llamar dentro del `except`) y devuelve el SignupError a lanzar."""
    ref = uuid.uuid4().hex[:8]
    log.error(
        "Registro falló en la fase '%s' (ref %s): %s",
        phase,
        ref,
        type(exc).__name__,
        exc_info=exc,
    )
    rollback(user_id, f"error en {phase} [{ref}]")
    security_event(
        "signup_failed",
        user_id=user_id,
        detail=f"{phase}: {type(exc).__name__} [{ref}]",
        severity="high",
    )
    return SignupError(ref)
