"""Registro de páginas de la app (permite navegar entre ellas con st.switch_page)."""

from __future__ import annotations

import streamlit as st

from src.ui import state
from src.ui.chat_page import chat_page
from src.ui.zone_map import zone_map_page

CHAT = st.Page(chat_page, title="Asistente", icon=":material/chat:", default=True)
MAP = st.Page(
    zone_map_page, title="Mapa de zonas", icon=":material/map:", url_path="mapa"
)


def available() -> list:
    pages = [CHAT, MAP]
    if state.is_admin():
        from src.ui.observability_page import observability_page

        pages.append(
            st.Page(
                observability_page,
                title="Observabilidad",
                icon=":material/monitoring:",
                url_path="observabilidad",
            )
        )
    return pages


def open_map(un: str) -> None:
    """Abre el mapa con el N° UN de la respuesta ya cargado."""
    st.session_state.map_un = un
    st.session_state.pop("map_un_input", None)
    st.switch_page(MAP)
