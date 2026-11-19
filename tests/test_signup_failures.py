"""Registro sin fallos silenciosos, bandera EMAIL_VERIFICATION_REQUIRED y cuentas creadas por CLI."""

import pytest

from src.security import auth, registration

PWD = "Bomberos-2026"


def _register(username="camila", email="camila@bomberos.cl"):
    return registration.register_user(
        username, "Camila Rojas", email, PWD, PWD, True, ip="10.0.0.1"
    )


def test_unexpected_error_is_logged_with_ref_and_rolled_back(env, monkeypatch, caplog):
    def boom(*a, **k):
        raise RuntimeError("fallo interno")

    monkeypatch.setattr(registration, "send_code", boom)
    with pytest.raises(registration.SignupError) as err:
        _register()
    ref = err.value.ref
    assert ref in str(err.value) and len(ref) == 8
    assert "camila" not in env.db["users"].docs  # sin cuenta huérfana
    failed = [d for k, d in env.events if k == "signup_failed"]
    assert failed and "enviar código: RuntimeError" in failed[0]["detail"]
    assert ref in failed[0]["detail"]
    assert any(ref in r.getMessage() and r.exc_info for r in caplog.records)


def test_rollback_failure_does_not_hide_original_error(env, monkeypatch, caplog):
    from src.security import signup_failure

    monkeypatch.setattr(
        registration, "send_code", lambda *a: (_ for _ in ()).throw(KeyError("x"))
    )
    monkeypatch.setattr(signup_failure, "get_db", lambda: None)  # rollback revienta
    with pytest.raises(registration.SignupError):
        _register()
    assert any("KeyError" in d["detail"] for k, d in env.events if k == "signup_failed")


def test_verification_disabled_activates_account(env):
    env.features.EMAIL_VERIFICATION_REQUIRED = False
    acc = _register()
    assert acc["requires"] is None
    doc = env.db["users"].docs["camila"]
    assert doc["email_verified"] is True and "pending_expires_at" not in doc
    assert [m[0] for m in env.mails] == ["welcome"]  # sin código
    assert auth.authenticate("camila", PWD)["requires"] is None


def test_required_verification_without_smtp_creates_nothing(env):
    env.features.mail_enabled = False
    with pytest.raises(ValueError, match="requiere el envío de correo"):
        _register()
    assert not env.db["users"].docs and not env.mails


def test_cli_accounts_are_verified(env, monkeypatch):
    from src.security import create_user as cli

    monkeypatch.setattr(cli.getpass, "getpass", lambda *a: PWD)
    monkeypatch.setattr(
        "sys.argv",
        ["x", "--username", "jefe", "--role", "admin", "--email", "jefe@b.cl"],
    )
    cli.main()
    doc = env.db["users"].docs["jefe"]
    assert doc["email_verified"] is True and doc["email"] == "jefe@b.cl"
    assert auth.authenticate("jefe", PWD)["requires"] == "privacy"
