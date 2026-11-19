"""Diagnóstico SMTP y detección de configuración inválida (sin red: smtplib simulado)."""

import smtplib
from typing import ClassVar

import pytest

from src.config.features import Features
from src.notify import mailer, smtp_check


def _features(user="yo@gmail.com", password="abcd efgh ijkl mnop"):
    return Features(SMTP_USER=user, SMTP_PASSWORD=password)


@pytest.mark.parametrize(
    ("user", "password", "problem"),
    [
        ("", "x", "faltan"),
        ("abcd efgh ijkl mnop", "abcd efgh ijkl mnop", "dirección de correo"),
        ("yo@gmail.com", "yo@gmail.com", "iguales"),
        ("yo@gmail.com", "abcd efgh ijkl mnop", None),
    ],
)
def test_mail_problem(user, password, problem):
    found = _features(user, password).mail_problem
    assert (found is None) if problem is None else (problem in found)


class FakeSMTP:
    error: Exception | None = None
    refused: ClassVar[dict] = {}

    def __init__(self, *a, **k):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def login(self, user, password):
        if FakeSMTP.error:
            raise FakeSMTP.error

    def send_message(self, msg):
        return FakeSMTP.refused


@pytest.fixture
def fake_smtp(monkeypatch):
    FakeSMTP.error, FakeSMTP.refused = None, {}
    monkeypatch.setattr(smtplib, "SMTP_SSL", FakeSMTP)
    for mod in (smtp_check, mailer):
        monkeypatch.setattr(mod, "features", _features())
    monkeypatch.setattr(mailer, "_log", lambda *a, **k: None)
    return FakeSMTP


def test_login_ok(fake_smtp):
    ok, message = smtp_check.check_login()
    assert ok and "Login OK" in message


def test_auth_error_has_hint(fake_smtp):
    fake_smtp.error = smtplib.SMTPAuthenticationError(535, b"bad")
    ok, message = smtp_check.check_login()
    assert not ok and "contraseña de aplicación" in message
    assert smtp_check.main([]) == 1


def test_invalid_config_is_reported_without_connecting(fake_smtp, monkeypatch):
    monkeypatch.setattr(smtp_check, "features", _features("abcd efgh", "abcd efgh"))
    ok, message = smtp_check.check_login()
    assert not ok and "Configuración inválida" in message


def test_refused_recipient_is_a_failure(fake_smtp):
    fake_smtp.refused = {"x@y.cl": (550, b"no")}
    assert not mailer.send(["x@y.cl"], "s", "<p>h</p>", "t", kind="smtp_test")
    fake_smtp.refused = {}
    assert mailer.send(["x@y.cl"], "s", "<p>h</p>", "t", kind="smtp_test")
