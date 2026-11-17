"""Página principal del asistente."""

from __future__ import annotations

import streamlit as st

from src.config.settings import settings
from src.ui import state
from src.ui.chat import ask, render_history
from src.ui.sidebar import render_sidebar
from src.ui.theme import brand
from src.utils.constants import EXAMPLE_QUERIES


def _empty_state() -> str | None:
    st.html(
        '<div class="hz-hero"><h1>¿Qué material está involucrado?</h1>'
        "<p>Consulta por N° UN, nombre del material o describe el incidente. "
        "Cada respuesta cita la página de la GRE 2024.</p></div>"
    )
    choice = st.pills(
        "Sugerencias",
        EXAMPLE_QUERIES,
        label_visibility="collapsed",
        key=f"suggest_{st.session_state.get('thread_id')}",
    )
    return choice


def chat_page() -> None:
    state.init_chat_state()
    render_sidebar()
    brand()

    suggestion = None
    if not st.session_state.get("history"):
        suggestion = _empty_state()
    render_history()

    prompt = st.chat_input(
        "Escribe un N° UN, un material o describe el incidente…",
        max_chars=settings.MAX_QUERY_CHARS,
    )
    query = prompt or suggestion
    if query:
        ask(query)
