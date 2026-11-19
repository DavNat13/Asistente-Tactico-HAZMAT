"""Restablecer la contraseña con un código enviado al correo verificado.

- Paso 1: la respuesta es SIEMPRE la misma y tarda lo mismo (piso de MIN_RESPONSE_S; el correo se
  envía en segundo plano), exista o no la cuenta. Así no se revela si un correo está registrado.
- Paso 2: código (`purpose: "reset"`) + nueva contraseña. Al cambiarla se desbloquea la cuenta, se
  invalidan todos los códigos del usuario, se guarda `password_changed_at` y se avisa por correo.
- Límites por correo y por IP (`st.context.ip_address`; si no hay IP, solo por correo).
"""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime

from src.observability.store import run_async, security_event
from src.security import otp, throttle
from src.security.accounts import _users, find_by_login, normalize_email
from src.security.passwords import hash_password, validate_password
from src.security.verification import send_code

log = logging.getLogger("hazmat.recovery")
GENERIC = "Si el correo está registrado y verificado, te enviamos un código"
INVALID = "El código no es válido o expiró. Revisa el correo o solicita uno nuevo"
TOO_MANY = "Demasiados intentos. Intenta más tarde"
MIN_RESPONSE_S = 1.2
MAX_REQUESTS_PER_EMAIL = 5
MAX_REQUESTS_PER_IP = 20
MAX_CONFIRMS_PER_IP = 30


def _eligible(email: str) -> dict | None:
    user = find_by_login(email)
    return user if user and user.get("email_verified") is True else None


def _send_async(user: dict) -> None:
    def _job():
        try:
            send_code(user, "reset")
        except Exception as e:  # noqa: BLE001 — espera o límite: la respuesta no cambia
            log.info("Código de recuperación no enviado: %s", type(e).__name__)

    run_async(_job)


def _request(email: str, ip: str | None) -> None:
    try:
        email = normalize_email(email)
    except ValueError:
        return
    if not throttle.allow("reset_ip", ip, MAX_REQUESTS_PER_IP):
        return
    if not throttle.allow("reset_email", email, MAX_REQUESTS_PER_EMAIL):
        return
    user = _eligible(email)
    if not user:
        security_event("reset_requested", detail="sin cuenta elegible", severity="low")
        return
    security_event("reset_requested", user_id=user["_id"], severity="low")
    _send_async(user)


def request_reset(email: str, ip: str | None = None) -> str:
    """Paso 1. Devuelve siempre GENERIC con un tiempo de respuesta uniforme."""
    t0 = time.monotonic()
    try:
        _request(email, ip)
    except Exception as e:  # noqa: BLE001 — ni siquiera un error revela algo
        log.warning("Fallo al solicitar recuperación: %s", type(e).__name__)
    wait = MIN_RESPONSE_S - (time.monotonic() - t0)
    if wait > 0:
        time.sleep(wait)
    return GENERIC


def reset_password(
    email: str, code: str, new: str, confirm: str, ip: str | None = None
) -> None:
    """Paso 2. Lanza ValueError con un mensaje que no revela si el correo existe."""
    if new != confirm:
        raise ValueError("Las contraseñas no coinciden")
    validate_password(new)
    if not throttle.allow("reset_confirm_ip", ip, MAX_CONFIRMS_PER_IP):
        raise ValueError(TOO_MANY)
    try:
        user = _eligible(normalize_email(email))
    except ValueError:
        user = None
    if not user:
        otp.hash_code(code or "", "-", "reset")  # tiempo similar al caso real
        security_event("reset_failed", detail="sin cuenta elegible", severity="low")
        raise ValueError(INVALID)
    if not otp.verify(user["_id"], "reset", code):
        raise ValueError(INVALID)
    _users().update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "password_hash": hash_password(new),
                "failed_attempts": 0,
                "locked_until": None,
                "password_changed_at": datetime.now(UTC),
            }
        },
    )
    otp.invalidate(user["_id"])
    security_event("password_reset", user_id=user["_id"], detail="contraseña cambiada")
    from src.notify.notifications import notify_password_changed

    notify_password_changed(user)
