"""Aviso de privacidad versionado: texto completo en `docs/AVISO_PRIVACIDAD.md`.

- `PRIVACY_VERSION` identifica el texto aceptado. Si cambia, se pide reaceptar al iniciar sesión.
- La aceptación guarda `privacy_version` y `privacy_accepted_at` en el usuario y un evento de seguridad.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path

from src.observability.store import security_event

PRIVACY_VERSION = "2026-12-01-v1"
PRIVACY_DATE = "1 de diciembre de 2026"
NOTICE_PATH = Path(__file__).resolve().parents[2] / "docs" / "AVISO_PRIVACIDAD.md"
MARKER = re.compile(r"\[\[[^\]]+\]\]")


@lru_cache(maxsize=1)
def load_notice() -> str:
    return NOTICE_PATH.read_text(encoding="utf-8")


def slug(title: str) -> str:
    t = unicodedata.normalize("NFKD", title.lower()).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


def split_sections(text: str) -> tuple[str, list[tuple[str, str, str]]]:
    """Separa el preámbulo y las secciones `## ...` → (preámbulo, [(ancla, título, cuerpo)])."""
    parts = re.split(r"^## +", text, flags=re.MULTILINE)
    sections = []
    for part in parts[1:]:
        title, _, body = part.partition("\n")
        sections.append((f"aviso-{slug(title)}", title.strip(), body.strip()))
    return parts[0].strip(), sections


def pending_markers(text: str | None = None) -> list[str]:
    """Marcadores `[[...]]` que el responsable debe completar antes de publicar."""
    return MARKER.findall(text if text is not None else load_notice())


def acceptance_fields() -> dict:
    return {
        "privacy_version": PRIVACY_VERSION,
        "privacy_accepted_at": datetime.now(UTC),
    }


def needs_acceptance(user: dict) -> bool:
    return user.get("privacy_version") != PRIVACY_VERSION


def accept(username: str) -> None:
    """Registra la aceptación de la versión vigente (reaceptación al iniciar sesión)."""
    from src.security.accounts import _users

    _users().update_one({"_id": username}, {"$set": acceptance_fields()})
    log_acceptance(username)


def log_acceptance(username: str) -> None:
    security_event(
        "privacy_accepted",
        user_id=username,
        detail=f"versión {PRIVACY_VERSION}",
        severity="low",
    )
