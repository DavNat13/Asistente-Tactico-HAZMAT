"""Registro de cuentas nuevas (rol `operador`) con verificación del correo.

Con `EMAIL_VERIFICATION_REQUIRED=false` (desarrollo) la cuenta queda activa sin código.
Ningún error inesperado es silencioso: ver `signup_failure.py` (log, evento y referencia).

- Nunca sobrescribe una cuenta existente (inserción con clave única → evita secuestro de cuentas).
- Usuario y correo únicos; valida nombre, correo y contraseña; exige aceptar el aviso de privacidad
  (se guarda `privacy_version` y `privacy_accepted_at`).
- Límites: 30 altas/hora en total, por IP y por correo. Cada alta queda auditada.
- Transaccional: la cuenta nace con `email_verified: False` y vence en 30 min. Si el código no se
  puede enviar, la cuenta se elimina y el registro NO se completa.
- Correo de una cuenta pendiente → aviso explícito para entrar y reenviar el código (SEGURIDAD_ETICA).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from src.config.features import features
from src.observability.store import get_db, security_event
from src.security import privacy, throttle
from src.security.accounts import USERS, create_user, normalize_email, public
from src.security.signup_failure import SignupError, failure, rollback  # noqa: F401
from src.security.validators import email_error, name_error, username_error
from src.security.verification import send_code

MAX_SIGNUPS_PER_HOUR = 30
MAX_SIGNUPS_PER_IP = 10
MAX_SIGNUPS_PER_EMAIL = 3
PENDING_MINUTES = 30
SEND_FAILED = "No pudimos enviar el código de verificación. Intenta más tarde"
THROTTLED = "Se alcanzó el límite de registros. Intenta más tarde"
MAIL_REQUIRED = (
    "El registro requiere el envío de correo, que no está configurado. "
    "Contacta al administrador"
)


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
        raise PendingVerification(pending_message())
    raise ValueError("Ese correo ya está registrado")


def pending_message() -> str:
    return (
        f"Ya hay un registro pendiente con este correo. Entra con tu usuario y contraseña "
        f"para reenviar el código, o espera a que venza ({PENDING_MINUTES} min)"
    )


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
    for error in (name_error(name), username_error(username), email_error(email)):
        if error:
            raise ValueError(error)
    name = " ".join(name.split())
    email = normalize_email(email)
    if password != confirm:
        raise ValueError("Las contraseñas no coinciden")
    required = features.EMAIL_VERIFICATION_REQUIRED
    if (
        required and not features.mail_enabled
    ):  # no crear cuentas que nadie podría activar
        security_event(
            "signup_blocked", detail="verificación sin SMTP", severity="high"
        )
        raise ValueError(MAIL_REQUIRED)
    _check_limits(email, ip)
    _existing_email(email)
    phase, user_id = "crear cuenta", None
    try:
        user = create_user(
            username, password, "operador", name, email=email, extra=_extra(required)
        )
        user_id = user["_id"]
        doc = {"_id": user_id, "name": user["name"], "email": user["email"]}
        account = public(doc | {"role": user["role"]})
        if not required:
            phase = "activar sin verificación"
            _audit(user_id, "activa (verificación desactivada)")
            from src.notify.notifications import notify_welcome

            notify_welcome(account)
            return {**account, "requires": None}
        phase = "enviar código"
        sent = send_code(doc, "signup")
    except ValueError:  # usuario/correo repetido o límite de códigos: mensaje claro
        rollback(user_id, "registro rechazado")
        raise
    except Exception as exc:
        raise failure(phase, exc, user_id) from exc
    if not sent:
        rollback(user_id, "código no enviado")
        raise ValueError(SEND_FAILED)
    _audit(user_id, "pendiente de verificación")
    return {**account, "requires": "verify"}


def _extra(required: bool) -> dict:
    pending = {
        "email_verified": False,
        "pending_expires_at": datetime.now(UTC) + timedelta(minutes=PENDING_MINUTES),
    }
    return {
        **(pending if required else {"email_verified": True}),
        **privacy.acceptance_fields(),
    }


def _audit(user_id: str, detail: str) -> None:
    security_event("signup", user_id=user_id, detail=detail, severity="low")
    privacy.log_acceptance(user_id)
