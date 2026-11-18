"""Registro de cuentas nuevas (rol `operador`).

- Nunca sobrescribe una cuenta existente (inserción con clave única → evita secuestro de cuentas).
- Usuario y correo únicos; valida nombre, correo y política de contraseña; exige aceptar la privacidad.
- Limita registros por ventana de tiempo (anti-abuso), audita cada alta y envía correo de bienvenida.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from src.observability.store import get_db, security_event
from src.security.accounts import USERS, create_user, normalize_email

MAX_SIGNUPS_PER_HOUR = 30


def register_user(
    username: str, name: str, email: str, password: str, confirm: str, accepted: bool
) -> dict:
    """Crea la cuenta y la devuelve lista para iniciar sesión. Lanza ValueError con un mensaje claro."""
    if not accepted:
        raise ValueError("Debes aceptar el aviso de privacidad para crear tu cuenta")
    name = (name or "").strip()
    if len(name) < 2:
        raise ValueError("Ingresa tu nombre")
    email = normalize_email(email)
    if password != confirm:
        raise ValueError("Las contraseñas no coinciden")
    since = datetime.now(UTC) - timedelta(hours=1)
    recent = get_db()[USERS].count_documents({"created_at": {"$gte": since}})
    if recent >= MAX_SIGNUPS_PER_HOUR:
        security_event(
            "signup_throttled", detail="límite horario de registros", severity="high"
        )
        raise ValueError("Se alcanzó el límite de registros. Intenta más tarde")
    user = create_user(username, password, role="operador", name=name, email=email)
    security_event(
        "signup", user_id=user["_id"], detail="cuenta creada", severity="low"
    )
    account = {
        "username": user["_id"],
        "name": user["name"],
        "role": user["role"],
        "email": user["email"],
    }
    from src.notify.notifications import notify_welcome

    notify_welcome(account)
    return account
