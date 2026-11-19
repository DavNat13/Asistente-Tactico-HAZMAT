"""Limpieza de código en mensajes y registro de cuentas (BD simulada en memoria, ver conftest)."""

import pytest

from src.security import registration
from src.security.text import strip_markup


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("<script>alert(1)</script>", ""),
        ("<script>alert(1)</script> ¿Guía del UN 1203?", "¿Guía del UN 1203?"),
        ("&lt;script&gt;alert(1)&lt;/script&gt;hola", "hola"),
        ("<img src=x onerror=alert(1)> cloro", "cloro"),
        ("<b>negrita</b> ok", "negrita ok"),
        ("<script>alert(1)", ""),
        ("[link](javascript:alert(1))", "[link](alert(1))"),
        ("Guía 128: aislar 50 m", "Guía 128: aislar 50 m"),
    ],
)
def test_strip_markup(raw, expected):
    assert strip_markup(raw) == expected


@pytest.fixture
def users(env):
    return env.db["users"]


def test_register_creates_operator(users):
    acc = registration.register_user(
        "Camila.R",
        "Camila Rojas",
        "Camila@Bomberos.cl",
        "Bomberos-2026",
        "Bomberos-2026",
        True,
    )
    assert acc == {
        "username": "camila.r",
        "name": "Camila Rojas",
        "role": "operador",
        "email": "camila@bomberos.cl",
        "requires": "verify",
    }
    assert users.docs["camila.r"]["password_hash"].startswith("scrypt$")


def test_register_never_overwrites_existing_account(users):
    registration.register_user(
        "admin", "Admin", "a@b.cl", "Original-123", "Original-123", True
    )
    original = users.docs["admin"]["password_hash"]
    with pytest.raises(ValueError, match="ya está registrado"):
        registration.register_user(
            "admin", "Atacante", "x@y.cl", "Hackeo-12345", "Hackeo-12345", True
        )
    assert users.docs["admin"]["password_hash"] == original


@pytest.mark.parametrize(
    ("args", "msg"),
    [
        (
            ("pedro", "Pedro", "p@b.cl", "Clave-12345", "Otra-123456", True),
            "no coinciden",
        ),
        (
            ("pedro", "Pedro", "p@b.cl", "Clave-12345", "Clave-12345", False),
            "aviso de privacidad",
        ),
        (("pedro", "", "p@b.cl", "Clave-12345", "Clave-12345", True), "nombre"),
        (
            ("pe", "Pedro", "p@b.cl", "Clave-12345", "Clave-12345", True),
            "al menos 3 caracteres",
        ),
        (("pedro", "Pedro", "p@b.cl", "corta", "corta", True), "al menos"),
    ],
)
def test_register_validation(users, args, msg):
    with pytest.raises(ValueError, match=msg):
        registration.register_user(*args)


def test_register_rejects_bad_or_duplicate_email(users):
    with pytest.raises(ValueError, match="correo válido"):
        registration.register_user(
            "ana", "Ana", "no-es-correo", "Clave-12345", "Clave-12345", True
        )
    registration.register_user(
        "ana", "Ana", "ana@b.cl", "Clave-12345", "Clave-12345", True
    )
    # Cuenta aún pendiente: solo "Revisa tu correo" (el caso verificado está en test_registration_verify)
    with pytest.raises(registration.PendingVerification, match="registro pendiente"):
        registration.register_user(
            "ana2", "Ana", "ANA@b.cl", "Clave-12345", "Clave-12345", True
        )
