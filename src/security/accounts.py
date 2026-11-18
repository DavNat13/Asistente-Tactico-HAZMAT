"""Cuentas de usuario (colección `users`): alta sin sobrescritura, correo único y búsqueda por login.

Roles: `operador` (chat) y `admin` (chat + dashboard de observabilidad).
"""

from __future__ import annotations

import logging
import re
from datetime import UTC, datetime

from pymongo.errors import DuplicateKeyError

from src.observability.store import get_db
from src.security.passwords import hash_password, validate_password
from src.session.sanitizer import InputSanitizer

log = logging.getLogger("hazmat.accounts")
USERS = "users"
ROLES = ("operador", "admin")
_EMAIL = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
_index_ready = False


def normalize_email(email: str) -> str:
    email = (email or "").strip().lower()
    if not _EMAIL.match(email) or len(email) > 120:
        raise ValueError("Ingresa un correo electrónico válido")
    return email


def _users():
    global _index_ready
    col = get_db()[USERS]
    if not _index_ready:
        try:  # correo único entre cuentas (índice parcial: cuentas antiguas sin correo)
            col.create_index(
                "email",
                unique=True,
                name="email_unique",
                partialFilterExpression={"email": {"$type": "string"}},
            )
            _index_ready = True
        except Exception as e:  # noqa: BLE001 — BD de pruebas sin soporte de índices
            log.debug("Índice de correo no creado: %s", e)
    return col


def create_user(
    username: str,
    password: str,
    role: str = "operador",
    name: str = "",
    overwrite: bool = False,
    email: str | None = None,
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
    if email:
        doc["email"] = normalize_email(email)
    if overwrite:  # solo el CLI de administración puede reemplazar una cuenta existente
        _users().replace_one({"_id": username}, doc, upsert=True)
    else:
        try:
            _users().insert_one(doc)
        except DuplicateKeyError as e:
            field = "correo" if "email" in str(e) else "nombre de usuario"
            raise ValueError(f"Ese {field} ya está registrado") from None
    return {
        "_id": username,
        "name": doc["name"],
        "role": role,
        "email": doc.get("email"),
    }


def find_by_login(login: str) -> dict | None:
    """Busca una cuenta activa por nombre de usuario o por correo."""
    login = (login or "").strip().lower()
    if "@" in login:
        try:
            return _users().find_one({"email": normalize_email(login), "active": True})
        except ValueError:
            return None
    try:
        return _users().find_one(
            {"_id": InputSanitizer.sanitize_username(login), "active": True}
        )
    except ValueError:
        return None
