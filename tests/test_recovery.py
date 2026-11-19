"""Recuperación de contraseña: respuesta uniforme y efectos del cambio."""

from datetime import UTC, datetime, timedelta

import pytest

from src.security import auth, otp, recovery
from src.security.accounts import create_user

OLD, NEW = "Original-2026", "Nueva-clave-2026"


@pytest.fixture
def account(env):
    create_user("ana", OLD, email="ana@bomberos.cl", extra={"email_verified": True})
    return env


def test_identical_response_for_existing_and_unknown_email(account):
    known = recovery.request_reset("ana@bomberos.cl", ip="1.1.1.1")
    unknown = recovery.request_reset("nadie@bomberos.cl", ip="1.1.1.1")
    malformed = recovery.request_reset("no-es-correo", ip="1.1.1.1")
    assert known == unknown == malformed == recovery.GENERIC
    assert [m[1] for m in account.mails] == ["ana@bomberos.cl"]


def test_unverified_account_gets_no_code(account):
    account.db["users"].docs["ana"]["email_verified"] = False
    assert recovery.request_reset("ana@bomberos.cl") == recovery.GENERIC
    assert not account.mails


def test_response_time_has_a_floor(account, monkeypatch):
    monkeypatch.setattr(recovery, "MIN_RESPONSE_S", 0.2)
    slept = []
    monkeypatch.setattr(recovery.time, "sleep", slept.append)
    recovery.request_reset("nadie@bomberos.cl")
    assert slept and 0 < slept[0] <= 0.2


def test_wrong_code_and_unknown_email_same_message(account):
    recovery.request_reset("ana@bomberos.cl")
    with pytest.raises(ValueError) as wrong:
        recovery.reset_password("ana@bomberos.cl", "123", NEW, NEW)
    with pytest.raises(ValueError) as unknown:
        recovery.reset_password("nadie@bomberos.cl", "123456", NEW, NEW)
    assert str(wrong.value) == str(unknown.value) == recovery.INVALID


def test_reset_changes_password_unlocks_and_invalidates_codes(account):
    users = account.db["users"].docs
    users["ana"].update(
        failed_attempts=3, locked_until=datetime.now(UTC) + timedelta(minutes=9)
    )
    signup_code = otp.issue("ana", "signup")
    recovery.request_reset("ana@bomberos.cl")
    code = account.mails[-1][2]
    recovery.reset_password("ana@bomberos.cl", code, NEW, NEW)
    doc = users["ana"]
    assert doc["failed_attempts"] == 0 and doc["locked_until"] is None
    assert doc["password_changed_at"] <= datetime.now(UTC)
    assert not otp.verify("ana", "signup", signup_code)  # todos los códigos invalidados
    with pytest.raises(ValueError):
        recovery.reset_password("ana@bomberos.cl", code, OLD, OLD)  # uso único
    assert auth.authenticate("ana", NEW) and not auth.authenticate("ana", OLD)
    assert ("changed", "ana@bomberos.cl", None) in account.mails
    assert all(code not in str(e) and NEW not in str(e) for e in account.events)


def test_new_password_must_follow_policy(account):
    with pytest.raises(ValueError, match="al menos"):
        recovery.reset_password("ana@bomberos.cl", "123456", "corta1", "corta1")
    with pytest.raises(ValueError, match="no coinciden"):
        recovery.reset_password("ana@bomberos.cl", "123456", NEW, NEW + "x")
