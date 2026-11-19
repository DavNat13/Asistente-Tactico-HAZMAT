"""Validación de los campos de registro: una sola fuente para la UI (en vivo) y el backend.

Cada función devuelve el mensaje de error o None si el valor es válido.
"""

from __future__ import annotations

import re

from src.security.passwords import MIN_PASSWORD

# Nombre: letras (con tildes), espacios, apóstrofo, guion y punto; al menos 2 letras.
_NAME = re.compile(r"^[A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ' .-]*$")
_USERNAME = re.compile(r"^[a-z0-9._-]{3,32}$")
# Correo: parte local sin puntos al inicio/fin ni dobles; dominio con etiquetas y TLD de letras.
_EMAIL = re.compile(
    r"^(?!\.)(?!.*\.\.)[A-Za-z0-9._%+-]{1,64}(?<!\.)@"
    r"(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,24}$"
)


def name_error(name: str | None) -> str | None:
    name = " ".join((name or "").split())
    if len(name) < 2:
        return "Ingresa tu nombre"
    if len(name) > 60:
        return "El nombre puede tener hasta 60 caracteres"
    if not _NAME.match(name) or sum(c.isalpha() for c in name) < 2:
        return "El nombre solo puede tener letras, espacios, apóstrofo o guion"
    return None


def username_error(username: str | None) -> str | None:
    value = (username or "").strip().lower()  # se guarda en minúsculas
    if len(value) < 3:
        return "El usuario debe tener al menos 3 caracteres"
    if len(value) > 32:
        return "El usuario puede tener hasta 32 caracteres"
    if not _USERNAME.match(value):
        return "Solo letras sin tildes, números, punto, guion o guion bajo"
    if not any(c.isalpha() for c in value):
        return "El usuario debe incluir al menos una letra"
    return None


def email_error(email: str | None) -> str | None:
    value = (email or "").strip()
    if not value:
        return "Ingresa tu correo electrónico"
    if len(value) > 120 or not _EMAIL.match(value):
        return "Ingresa un correo válido, por ejemplo nombre@dominio.cl"
    return None


def password_rules(password: str, confirm: str | None = None) -> list[tuple[bool, str]]:
    """Requisitos de contraseña (misma política que `validate_password`)."""
    rules = [
        (len(password) >= MIN_PASSWORD, f"Mínimo {MIN_PASSWORD} caracteres"),
        (
            bool(password) and not (password.isalpha() or password.isdigit()),
            "Letras y números o símbolos",
        ),
        (
            password.strip() == password and bool(password),
            "Sin espacios al inicio o final",
        ),
    ]
    if confirm is not None:
        rules.append(
            (bool(password) and password == confirm, "Las contraseñas coinciden")
        )
    return rules


def signup_errors(
    name: str, username: str, email: str, password: str, confirm: str
) -> dict[str, str]:
    """Errores por campo; vacío si todo es válido."""
    errors = {
        "name": name_error(name),
        "username": username_error(username),
        "email": email_error(email),
    }
    failed = [
        label for ok, label in password_rules(password or "", confirm or "") if not ok
    ]
    errors["password"] = failed[0] if failed else None
    return {k: v for k, v in errors.items() if v}
