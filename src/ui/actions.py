"""Barra de acciones bajo cada respuesta técnica: mapa, checklist y ficha de incidente."""

from __future__ import annotations

import re

import streamlit as st

from src.ui import incident_state
from src.ui.incident_dialog import incident_dialog

_UN = re.compile(r"\bUN\s?(\d{4})\b")


def first_un(text: str) -> str | None:
    for match in _UN.findall(text or ""):
        if 1001 <= int(match) <= 3599:
            return match
    return None


def _is_plan(msg: dict) -> bool:
    content = msg.get("content", "")
    return msg.get("complexity") == "high" or content.count("**") >= 8


def render_actions(msg: dict, key: str) -> None:
    content = msg.get("content", "")
    if not msg.get("sources") or "No encontré" in content[:80]:
        return  # rechazos, saludos o respuestas sin fuentes no tienen acciones
    un = first_un(content)
    with st.container(horizontal=True, key=f"actions_{key}", gap="small"):
        if un and st.button(
            "Ver en el mapa", icon=":material/map:", key=f"map_{key}", type="tertiary"
        ):
            from src.ui.pages import open_map

            open_map(un)
        if (
            _is_plan(msg)
            and not incident_state.current()
            and st.button(
                "Iniciar checklist",
                icon=":material/checklist:",
                key=f"startchk_{key}",
                type="tertiary",
            )
        ):
            incident_state.start(
                content, un, f"Incidente UN {un}" if un else "Incidente HAZMAT"
            )
            st.rerun()
        if st.button(
            "Ficha de incidente",
            icon=":material/description:",
            key=f"pdf_{key}",
            type="tertiary",
        ):
            incident_dialog(msg, un)
