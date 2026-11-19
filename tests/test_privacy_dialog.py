"""Aviso de privacidad: aceptación versionada y documento completo (secciones 0 a 19)."""

import re
import warnings

from src.security import auth, privacy, registration, verification

PWD = "Bomberos-2026"


def test_signup_stores_privacy_version_and_date(env):
    registration.register_user("ana", "Ana", "ana@b.cl", PWD, PWD, True)
    doc = env.db["users"].docs["ana"]
    assert doc["privacy_version"] == privacy.PRIVACY_VERSION
    assert doc["privacy_accepted_at"] is not None
    assert any(kind == "privacy_accepted" for kind, _ in env.events)


def test_version_change_requires_reacceptance(env, monkeypatch):
    registration.register_user("ana", "Ana", "ana@b.cl", PWD, PWD, True)
    verification.confirm("ana", env.mails[-1][2])
    assert auth.authenticate("ana", PWD)["requires"] is None
    monkeypatch.setattr(privacy, "PRIVACY_VERSION", "2027-01-01-v2")
    assert auth.authenticate("ana", PWD)["requires"] == "privacy"
    privacy.accept("ana")
    assert env.db["users"].docs["ana"]["privacy_version"] == "2027-01-01-v2"
    assert auth.authenticate("ana", PWD)["requires"] is None


def test_notice_has_all_sections_0_to_19():
    text = privacy.load_notice()
    numbers = [int(n) for n in re.findall(r"^## (\d+)\. ", text, flags=re.MULTILINE)]
    assert numbers == list(range(20))
    _, sections = privacy.split_sections(text)
    assert len(sections) == 20 and all(body for _, _, body in sections)
    assert (
        len({anchor for anchor, _, _ in sections}) == 20
    )  # anclas únicas para el índice


def test_notice_metadata_and_draft_mark():
    text = privacy.load_notice()
    assert "Borrador: revisión legal pendiente" in text
    assert privacy.PRIVACY_VERSION in text
    for law in ("19.628", "21.719", "21.663", "21.459", "artículo 19 número 4"):
        assert law in text


def test_pending_markers_are_warnings_not_failures():
    markers = privacy.pending_markers()
    if markers:
        warnings.warn(
            f"Aviso de privacidad: {len(markers)} marcadores [[...]] por completar",
            UserWarning,
            stacklevel=1,
        )
    assert privacy.pending_markers("sin marcadores") == []
    assert privacy.pending_markers("a [[X]] b [[Y: z]]") == ["[[X]]", "[[Y: z]]"]
