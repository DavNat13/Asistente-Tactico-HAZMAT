"""Consulta a partir de una foto: placa naranja / rombo → N° UN → consulta normal al agente."""

from __future__ import annotations

import streamlit as st

from src.agent.vision import ImageError, identify_un
from src.observability.store import security_event


def photo_query(file, text: str | None) -> str | None:
    """Devuelve la consulta a enviar o None si no se reconoció el N° UN (con aviso al usuario)."""
    text = (text or "").strip()
    with st.status("Analizando la foto de la placa…", expanded=False) as status:
        try:
            result = identify_un(file.getvalue())
        except ImageError as e:
            status.update(label=str(e), state="error")
            return None
        except Exception:  # noqa: BLE001 — servicio de visión no disponible
            status.update(
                label="No se pudo analizar la imagen. Intenta de nuevo.", state="error"
            )
            return None
        un = result["un"]
        if not un:
            status.update(
                label="No se encontró un N° UN legible en la foto.", state="error"
            )
            st.toast(
                "Prueba con una foto más cercana y de frente a la placa naranja.",
                icon=":material/photo_camera:",
            )
            return None
        status.update(
            label=f"Placa reconocida: UN {un} (confianza {result['confianza']})",
            state="complete",
        )
    security_event(
        "vision_query",
        detail=f"un={un} confianza={result['confianza']}",
        severity="low",
    )
    pregunta = (
        text or "¿Qué material es, qué guía aplica y qué distancias debo considerar?"
    )
    return f"[Foto de placa: UN {un}] {pregunta}"
