"""Página principal del asistente (estilo asistentes de IA: bienvenida, sugerencias, chat)."""

from __future__ import annotations

import html
from datetime import UTC, datetime

import streamlit as st

from src.config.settings import settings
from src.ui import state
from src.ui.chat import ask, render_history
from src.ui.sidebar import render_sidebar
from src.ui.theme import mark
from src.utils.constants import SUGGESTIONS


def _greeting() -> str:
    hour = datetime.now(UTC).astimezone().hour
    return (
        "Buenos días"
        if hour < 12
        else "Buenas tardes"
        if hour < 20
        else "Buenas noches"
    )


def _welcome() -> str | None:
    user = state.user() or {}
    first = html.escape((user.get("name") or "").split(" ")[0])
    st.html(
        f'<div class="hz-hero">{mark()}'
        f"<h1>{_greeting()}{', ' if first else ''}<span>{first}</span></h1>"
        "<p>Pregunta por un N° UN, un material o describe el incidente. "
        "Cada respuesta cita la página de la GRE 2024.</p></div>"
    )
    chosen = None
    cols = st.columns(2, gap="small")
    for i, (icon, label, query) in enumerate(SUGGESTIONS):
        with cols[i % 2]:
            if st.button(label, icon=icon, key=f"sug_{i}", width="stretch"):
                chosen = query
    return chosen


def chat_page() -> None:
    state.init_chat_state()
    render_sidebar()
    if flash := st.session_state.pop("flash", None):
        st.toast(flash, icon=":material/check_circle:")

    suggestion = _welcome() if not st.session_state.get("history") else None
    render_history()

    prompt = st.chat_input(
        "Pregunta al Asistente HAZMAT…", max_chars=settings.MAX_QUERY_CHARS
    )
    with st.bottom:  # aviso bajo la caja de texto
        st.html(
            '<p class="hz-disclaimer">Herramienta de apoyo. Verifica en la GRE impresa y '
            "sigue al mando del incidente.</p>"
        )
    if query := (prompt or suggestion):
        ask(query)
