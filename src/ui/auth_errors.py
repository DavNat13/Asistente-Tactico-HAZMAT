"""Errores inesperados en la pantalla de acceso: siempre con traceback en el log, un evento de
seguridad y una referencia corta que el usuario puede informar. Nunca se muestra el detalle interno.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

import streamlit as st

from src.observability.store import security_event

log = logging.getLogger("hazmat.auth_ui")


def report(exc: BaseException, where: str) -> str:
    """Registra el error (llamar dentro del `except`) y devuelve el mensaje para el usuario."""
    ref = uuid.uuid4().hex[:8]
    log.error("Error en %s (ref %s): %s", where, ref, type(exc).__name__, exc_info=exc)
    security_event(
        "auth_ui_error",
        detail=f"{where}: {type(exc).__name__} [{ref}]",
        severity="high",
    )
    return (
        f"Ocurrió un error inesperado (ref. {ref}). "
        "Intenta de nuevo o avisa al administrador"
    )


def local_now() -> datetime:
    """Hora en la zona del navegador (para "vence a las HH:MM"); UTC si no se conoce."""
    try:
        from zoneinfo import ZoneInfo

        return datetime.now(ZoneInfo(st.context.timezone or "UTC"))
    except Exception:  # noqa: BLE001 — zona desconocida o sin contexto
        return datetime.now(UTC)
