"""Registro transaccional con verificación de correo, migración y limpieza de pendientes."""

from datetime import UTC, datetime, timedelta

import pytest

from src.security import auth, migrate_verification, registration, verification

PWD = "Bomberos-2026"


def _register(username="camila", email="camila@bomberos.cl"):
    return registration.register_user(
        username, "Camila Rojas", email, PWD, PWD, True, ip="10.0.0.1"
    )


def _code(env):
    return [m for m in env.mails if m[0] == "signup"][-1][2]


def test_smtp_failure_rolls_back_account(env):
    env.smtp_ok = False
    with pytest.raises(ValueError, match="No pudimos enviar el código"):
        _register()
    assert "camila" not in env.db["users"].docs
    assert not env.db["email_tokens"].docs


def test_signup_creates_pending_account_without_welcome(env):
    acc = _register()
    assert acc["requires"] == "verify"
    doc = env.db["users"].docs["camila"]
    assert doc["email_verified"] is False
    assert doc["pending_expires_at"] > datetime.now(UTC) + timedelta(minutes=29)
    assert [m[0] for m in env.mails] == ["signup"]  # bienvenida recién al verificar


def test_no_login_until_verified(env):
    _register()
    assert auth.authenticate("camila", PWD)["requires"] == "verify"
    assert verification.confirm("camila", "abcdef") is None
    account = verification.confirm("camila", _code(env))
    assert account["username"] == "camila"
    assert auth.authenticate("camila@bomberos.cl", PWD)["requires"] is None
    assert "pending_expires_at" not in env.db["users"].docs["camila"]
    assert ("welcome", "camila@bomberos.cl", None) in env.mails


def test_pending_email_only_says_check_inbox(env):
    _register()
    with pytest.raises(registration.PendingVerification, match="registro pendiente"):
        _register(username="otra")
    verification.confirm("camila", _code(env))
    with pytest.raises(ValueError, match="Ese correo ya está registrado"):
        _register(username="otra")


def test_signup_limit_per_email(env):
    for _ in range(registration.MAX_SIGNUPS_PER_EMAIL):
        _register()
        verification.cancel_pending("camila")  # "Cambiar correo"
    with pytest.raises(ValueError, match="límite de registros"):
        _register()


def test_resend_respects_cooldown(env):
    _register()
    with pytest.raises(ValueError, match="Espera"):
        verification.resend("camila")


def test_purge_removes_only_expired_signups(env):
    _register()
    env.db["users"].docs["camila"]["pending_expires_at"] = datetime.now(
        UTC
    ) - timedelta(minutes=1)
    env.db["users"].insert_one({"_id": "legacy", "email_verified": False})
    assert verification.purge_unverified() == 1
    assert set(env.db["users"].docs) == {"legacy"}


def test_migration_and_account_without_email(env, monkeypatch):
    from src.security.accounts import create_user

    create_user("jefe", PWD, role="admin", email="jefe@bomberos.cl")
    create_user("viejo", PWD)
    assert migrate_verification.summary()["sin_correo"] == 1
    monkeypatch.setattr(
        migrate_verification, "features", type("F", (), {"mail_enabled": False})
    )
    with pytest.raises(RuntimeError, match="SMTP"):
        migrate_verification.apply()
    monkeypatch.setattr(
        migrate_verification, "features", type("F", (), {"mail_enabled": True})
    )
    assert migrate_verification.apply() == 2
    assert auth.authenticate("jefe", PWD)["requires"] == "verify"
    assert auth.authenticate("viejo", PWD)["requires"] == "email"
    assert verification.set_email("viejo", "viejo@bomberos.cl")
    assert verification.confirm("viejo", _code(env))
    assert auth.authenticate("viejo", PWD)["requires"] == "privacy"  # aviso nuevo
    assert migrate_verification.verify_user("jefe")  # vía de escape del operador
    assert auth.authenticate("jefe", PWD)["requires"] == "privacy"
