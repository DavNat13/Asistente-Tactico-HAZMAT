"""Configuración de las funciones automatizadas (correo, mapa, visión, alertas). Todo desde el entorno."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def _float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


def _list(name: str) -> list[str]:
    return [x.strip() for x in os.getenv(name, "").split(",") if x.strip()]


@dataclass(frozen=True)
class Features:
    # Día/noche para Tabla 1 (hora local)
    DAY_START: int = _int("DAY_START", 7)
    DAY_END: int = _int("DAY_END", 19)
    # Correo (Gmail SMTP con contraseña de aplicación)
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = _int("SMTP_PORT", 465)
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    MAIL_FROM: str = os.getenv("MAIL_FROM", "") or os.getenv("SMTP_USER", "")
    ADMIN_EMAILS: list[str] = field(default_factory=lambda: _list("ADMIN_EMAILS"))
    MAIL_MAX_PER_HOUR: int = _int("MAIL_MAX_PER_HOUR", 5)
    APP_URL: str = os.getenv("APP_URL", "http://localhost:8501")
    # Mapa (OpenStreetMap / Nominatim)
    GEOCODER_URL: str = os.getenv(
        "GEOCODER_URL", "https://nominatim.openstreetmap.org/search"
    )
    GEOCODER_COUNTRY: str = os.getenv("GEOCODER_COUNTRY", "cl")
    # Visión
    VISION_MODEL: str = os.getenv("VISION_MODEL", "gemini-3.5-flash-lite")
    MAX_IMAGE_MB: int = _int("MAX_IMAGE_MB", 5)
    # Alertas de salud
    ALERT_P95_S: float = _float("ALERT_P95_S", 20.0)
    ALERT_ERROR_RATE: float = _float("ALERT_ERROR_RATE", 0.05)
    ALERT_BLOCKED_RATE: float = _float("ALERT_BLOCKED_RATE", 0.30)
    ALERT_WINDOW_MIN: int = _int("ALERT_WINDOW_MIN", 30)
    ALERT_COOLDOWN_H: int = _int("ALERT_COOLDOWN_H", 6)

    @property
    def mail_enabled(self) -> bool:
        return bool(self.SMTP_USER and self.SMTP_PASSWORD)


features = Features()
