"""Limpieza de código en mensajes y registro de cuentas (BD simulada en memoria)."""

import pytest
from pymongo.errors import DuplicateKeyError

from src.security import auth, registration
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


class FakeUsers:
    def __init__(self):
        self.docs = {}

    def insert_one(self, doc):
        if doc["_id"] in self.docs:
            raise DuplicateKeyError("dup")
        self.docs[doc["_id"]] = doc

    def replace_one(self, flt, doc, upsert=False):
        self.docs[flt["_id"]] = doc

    def count_documents(self, flt):
        return len(self.docs)


@pytest.fixture
def users(monkeypatch):
    col = FakeUsers()
    db = {auth.USERS: col}
    monkeypatch.setattr(auth, "get_db", lambda: db)
    monkeypatch.setattr(registration, "get_db", lambda: db)
    monkeypatch.setattr(registration, "security_event", lambda *a, **k: None)
    return col


def test_register_creates_operator(users):
    acc = registration.register_user(
        "Camila.R", "Camila Rojas", "Bomberos-2026", "Bomberos-2026", True
    )
    assert acc == {"username": "camila.r", "name": "Camila Rojas", "role": "operador"}
    assert users.docs["camila.r"]["password_hash"].startswith("scrypt$")


def test_register_never_overwrites_existing_account(users):
    registration.register_user("admin", "Admin", "Original-123", "Original-123", True)
    original = users.docs["admin"]["password_hash"]
    with pytest.raises(ValueError, match="ya está registrado"):
        registration.register_user(
            "admin", "Atacante", "Hackeo-12345", "Hackeo-12345", True
        )
    assert users.docs["admin"]["password_hash"] == original


@pytest.mark.parametrize(
    ("args", "msg"),
    [
        (("pedro", "Pedro", "Clave-12345", "Otra-123456", True), "no coinciden"),
        (
            ("pedro", "Pedro", "Clave-12345", "Clave-12345", False),
            "aviso de privacidad",
        ),
        (("pedro", "", "Clave-12345", "Clave-12345", True), "nombre"),
        (("pe", "Pedro", "Clave-12345", "Clave-12345", True), "Usuario inválido"),
        (("pedro", "Pedro", "corta", "corta", True), "al menos"),
    ],
)
def test_register_validation(users, args, msg):
    with pytest.raises(ValueError, match=msg):
        registration.register_user(*args)
