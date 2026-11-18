"""Registro de cuentas nuevas (rol `operador`).

- Nunca sobrescribe una cuenta existente (inserción con clave única → evita secuestro de cuentas).
- Valida usuario, nombre y política de contraseña; exige aceptar el aviso de privacidad.
- Limita registros por ventana de tiempo (anti-abuso) y audita cada alta.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from src.observability.store import get_db, security_event
from src.security.auth import USERS, create_user

MAX_SIGNUPS_PER_HOUR = 30


def register_user(
    username: str, name: str, password: str, confirm: str, accepted: bool
) -> dict:
    """Crea la cuenta y la devuelve lista para iniciar sesión. Lanza ValueError con un mensaje claro."""
    if not accepted:
        raise ValueError("Debes aceptar el aviso de privacidad para crear tu cuenta")
    if password != confirm:
        raise ValueError("Las contraseñas no coinciden")
    name = (name or "").strip()
    if len(name) < 2:
        raise ValueError("Ingresa tu nombre")
    since = datetime.now(UTC) - timedelta(hours=1)
    if (
        get_db()[USERS].count_documents({"created_at": {"$gte": since}})
        >= MAX_SIGNUPS_PER_HOUR
    ):
        security_event(
            "signup_throttled", detail="límite horario de registros", severity="high"
        )
        raise ValueError("Se alcanzó el límite de registros. Intenta más tarde")
    user = create_user(username, password, role="operador", name=name)
    security_event(
        "signup", user_id=user["_id"], detail="cuenta creada", severity="low"
    )
    return {"username": user["_id"], "name": user["name"], "role": user["role"]}
