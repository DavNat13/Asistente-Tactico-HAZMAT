"""Configuración común: raíz del proyecto en sys.path y variables mínimas para importar settings."""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("GEMINI_API_KEYS", "test-key")
os.environ.setdefault("MONGODB_URI", "mongodb://localhost:27017/test")
os.environ.setdefault("GUARDRAIL_LLM", "false")

import pytest

from tests.fakedb import FakeDB

_DB_MODULES = ("accounts", "registration", "otp", "throttle")
_EVENT_MODULES = (
    "otp",
    "throttle",
    "verification",
    "registration",
    "recovery",
    "privacy",
    "auth",
    "migrate_verification",
)


@pytest.fixture
def env(monkeypatch):
    """BD en memoria + eventos de seguridad y correos capturados (sin red ni SMTP)."""
    import importlib
    from types import SimpleNamespace

    from src.notify import notifications

    db, events, mails = FakeDB(), [], []
    for name in set(_DB_MODULES + _EVENT_MODULES):
        mod = importlib.import_module(f"src.security.{name}")
        if hasattr(mod, "get_db"):
            monkeypatch.setattr(mod, "get_db", lambda: db)
        if hasattr(mod, "security_event"):
            monkeypatch.setattr(
                mod, "security_event", lambda kind, **k: events.append((kind, k))
            )
    state = SimpleNamespace(db=db, events=events, mails=mails, smtp_ok=True)

    def fake_send_code(user, code, purpose):
        mails.append((purpose, user["email"], code))
        return state.smtp_ok

    monkeypatch.setattr(notifications, "send_code", fake_send_code)
    monkeypatch.setattr(
        notifications,
        "notify_welcome",
        lambda u: mails.append(("welcome", u["email"], None)),
    )
    monkeypatch.setattr(
        notifications,
        "notify_password_changed",
        lambda u: mails.append(("changed", u["email"], None)),
    )
    from src.security import accounts, recovery, throttle

    monkeypatch.setattr(accounts, "_index_ready", True)
    monkeypatch.setattr(recovery, "MIN_RESPONSE_S", 0)
    monkeypatch.setattr(recovery, "run_async", lambda fn, *a: fn(*a))
    throttle.reset_local()
    return state
