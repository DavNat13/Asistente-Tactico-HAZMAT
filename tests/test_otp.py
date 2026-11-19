"""Códigos de verificación: formato, hash, expiración, intentos, uso único y comparación constante."""

from datetime import UTC, datetime, timedelta

from src.security import otp


def test_code_has_six_digits_with_leading_zeros(monkeypatch):
    monkeypatch.setattr(otp.secrets, "randbelow", lambda n: 42)
    assert otp.generate_code() == "000042"
    monkeypatch.undo()
    for _ in range(200):
        code = otp.generate_code()
        assert len(code) == 6 and code.isdigit()


def test_only_hmac_is_stored(env):
    code = otp.issue("ana", "signup")
    doc = env.db[otp.TOKENS].docs["signup:ana"]
    assert code not in str(doc.values())
    assert doc["code_hash"] == otp.hash_code(code, "ana", "signup")
    assert len(doc["code_hash"]) == 64
    assert (
        otp.hash_code(code, "ana", "reset") != doc["code_hash"]
    )  # ligado al propósito
    assert set(doc) >= {
        "user_id",
        "purpose",
        "created_at",
        "expires_at",
        "attempts",
        "last_sent_at",
        "used_at",
    }


def test_expiration_minutes(env):
    otp.issue("ana", "signup")
    otp.issue("ana", "reset")
    col = env.db[otp.TOKENS].docs
    for purpose, minutes in (("signup", 15), ("reset", 10)):
        doc = col[f"{purpose}:ana"]
        assert doc["expires_at"] - doc["created_at"] == timedelta(minutes=minutes)


def test_valid_code_is_single_use(env):
    code = otp.issue("ana", "signup")
    assert otp.verify("ana", "signup", code)
    assert not otp.verify("ana", "signup", code)


def test_expired_code_is_rejected(env):
    code = otp.issue("ana", "reset")
    env.db[otp.TOKENS].docs["reset:ana"]["expires_at"] = datetime.now(UTC) - timedelta(
        seconds=1
    )
    assert not otp.verify("ana", "reset", code)


def test_fifth_failure_invalidates_code(env):
    code = otp.issue("ana", "signup")
    wrong = "000000" if code != "000000" else "111111"
    for _ in range(otp.MAX_ATTEMPTS):
        assert not otp.verify("ana", "signup", wrong)
    assert not otp.verify(
        "ana", "signup", code
    )  # ni el correcto sirve: pedir uno nuevo
    assert env.db[otp.TOKENS].docs["signup:ana"]["attempts"] == otp.MAX_ATTEMPTS


def test_uses_constant_time_comparison(env, monkeypatch):
    calls = []
    real = otp.hmac.compare_digest
    monkeypatch.setattr(
        otp.hmac, "compare_digest", lambda a, b: calls.append(1) or real(a, b)
    )
    code = otp.issue("ana", "signup")
    assert otp.verify("ana", "signup", code)
    assert calls


def test_resend_cooldown(env):
    otp.issue("ana", "signup")
    assert 55 <= otp.cooldown_left("ana", "signup") <= otp.RESEND_COOLDOWN_S
    env.db[otp.TOKENS].docs["signup:ana"]["last_sent_at"] -= timedelta(seconds=61)
    assert otp.cooldown_left("ana", "signup") == 0


def test_invalidate_and_events_never_contain_code(env):
    code = otp.issue("ana", "signup")
    otp.verify("ana", "signup", "999999" if code != "999999" else "888888")
    otp.invalidate("ana")
    assert not otp.verify("ana", "signup", code)
    assert env.events and all(code not in str(e) for e in env.events)
