"""Registro de cuentas nuevas (rol `operador`) con verificación obligatoria del correo.

- Nunca sobrescribe una cuenta existente (inserción con clave única → evita secuestro de cuentas).
- Usuario y correo únicos; valida nombre, correo y contraseña; exige aceptar el aviso de privacidad
  (se guarda `privacy_version` y `privacy_accepted_at`).
- Límites: 30 altas/hora en total, por IP y por correo. Cada alta queda auditada.
- Transaccional: la cuenta nace con `email_verified: False` y vence en 30 min. Si el código no se
  puede enviar, la cuenta se elimina y el registro NO se completa.
- Correo de una cuenta pendiente → solo "Revisa tu correo" (decisión documentada en SEGURIDAD_ETICA).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from src.observability.store import get_db, security_event
from src.security import otp, privacy, throttle
from src.security.accounts import USERS, create_user, normalize_email, public
from src.security.verification import send_code

MAX_SIGNUPS_PER_HOUR = 30
MAX_SIGNUPS_PER_IP = 10
MAX_SIGNUPS_PER_EMAIL = 3
PENDING_MINUTES = 30
SEND_FAILED = "No pudimos enviar el código de verificación. Intenta más tarde"
THROTTLED = "Se alcanzó el límite de registros. Intenta más tarde"


class PendingVerification(ValueError):
    """El correo pertenece a una cuenta aún no verificada: no se dan más detalles."""


def _check_limits(email: str, ip: str | None) -> None:
    since = datetime.now(UTC) - timedelta(hours=1)
    recent = get_db()[USERS].count_documents({"created_at": {"$gte": since}})
    if recent >= MAX_SIGNUPS_PER_HOUR:
        security_event(
            "signup_throttled", detail="límite horario global", severity="high"
        )
        raise ValueError(THROTTLED)
    if not throttle.allow("signup_ip", ip, MAX_SIGNUPS_PER_IP) or not throttle.allow(
        "signup_email", email, MAX_SIGNUPS_PER_EMAIL
    ):
        raise ValueError(THROTTLED)


def _existing_email(email: str) -> None:
    found = get_db()[USERS].find_one({"email": email})
    if not found:
        return
    if found.get("email_verified") is False:
        raise PendingVerification("Revisa tu correo")
    raise ValueError("Ese correo ya está registrado")


def register_user(
    username: str,
    name: str,
    email: str,
    password: str,
    confirm: str,
    accepted: bool,
    ip: str | None = None,
) -> dict:
    """Crea la cuenta PENDIENTE y envía el código. Lanza ValueError con un mensaje claro."""
    if not accepted:
        raise ValueError("Debes aceptar el aviso de privacidad para crear tu cuenta")
    name = (name or "").strip()
    if len(name) < 2:
        raise ValueError("Ingresa tu nombre")
    email = normalize_email(email)
    if password != confirm:
        raise ValueError("Las contraseñas no coinciden")
    _check_limits(email, ip)
    _existing_email(email)
    extra = {
        "email_verified": False,
        "pending_expires_at": datetime.now(UTC) + timedelta(minutes=PENDING_MINUTES),
        **privacy.acceptance_fields(),
    }
    user = create_user(username, password, "operador", name, email=email, extra=extra)
    doc = {"_id": user["_id"], "name": user["name"], "email": user["email"]}
    try:
        sent = send_code(doc, "signup")
    except Exception:  # noqa: BLE001 — cualquier fallo de envío anula el registro
        sent = False
    if not sent:
        get_db()[USERS].delete_one({"_id": user["_id"], "email_verified": False})
        otp.delete_for(user["_id"])
        security_event(
            "signup_rolled_back", user_id=user["_id"], detail="código no enviado"
        )
        raise ValueError(SEND_FAILED)
    security_event(
        "signup",
        user_id=user["_id"],
        detail="pendiente de verificación",
        severity="low",
    )
    privacy.log_acceptance(user["_id"])
    return {**public(doc | {"role": user["role"]}), "requires": "verify"}
