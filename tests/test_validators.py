"""Validadores de registro (los mismos que usa la UI en vivo y el backend)."""

import pytest

from src.security import registration
from src.security.validators import (
    email_error,
    name_error,
    password_rules,
    signup_errors,
    username_error,
)


@pytest.mark.parametrize(
    "email", ["ana@bomberos.cl", "a.b+x@sub.dominio.com", "J_P@b-c.org"]
)
def test_valid_emails(email):
    assert email_error(email) is None


@pytest.mark.parametrize(
    "email",
    [
        "",
        "dsadas",
        "a@b",
        "a@b.c",
        ".a@b.cl",
        "a.@b.cl",
        "a..b@c.cl",
        "a@-b.cl",
        "a@b..cl",
        "a b@c.cl",
        "a@b.c1",
    ],
)
def test_invalid_emails(email):
    assert email_error(email)


@pytest.mark.parametrize(
    ("value", "ok"),
    [
        ("Camila Rojas", True),
        ("José O'Higgins-Pérez", True),
        ("A", False),
        ("123", False),
        ("Ana <b>", False),
        ("..", False),
    ],
)
def test_names(value, ok):
    assert (name_error(value) is None) == ok


@pytest.mark.parametrize(
    ("value", "ok"),
    [
        ("camila.rojas", True),
        ("jp_2026", True),
        ("ab", False),
        ("Camila.R", True),
        ("josé", False),
        ("a b", False),
        ("1234", False),
    ],
)
def test_usernames(value, ok):
    assert (username_error(value) is None) == ok


def test_password_rules_and_signup_errors():
    assert all(ok for ok, _ in password_rules("Bomberos-2026", "Bomberos-2026"))
    failed = [label for ok, label in password_rules("dasdas", "sadas") if not ok]
    assert len(failed) == 3  # largo, combinación y coincidencia
    assert not all(ok for ok, _ in password_rules(" Bomberos-2026", None))
    errs = signup_errors("dasdasda", "asdasda", "dsadas", "dasdas", "sadas")
    assert set(errs) == {"email", "password"}
    assert (
        signup_errors("Ana Rojas", "ana", "ana@b.cl", "Clave-12345", "Clave-12345")
        == {}
    )


def test_backend_rejects_what_the_ui_rejects(env):
    with pytest.raises(ValueError, match="correo válido"):
        registration.register_user(
            "ana", "Ana", "dsadas", "Clave-12345", "Clave-12345", True
        )
    with pytest.raises(ValueError, match="letras"):
        registration.register_user(
            "ana", "123", "a@b.cl", "Clave-12345", "Clave-12345", True
        )
    with pytest.raises(ValueError, match="espacios"):
        registration.register_user(
            "ana", "Ana", "a@b.cl", " Clave-12345", " Clave-12345", True
        )
    assert not env.db["users"].docs
