"""Barra lateral estilo asistentes de IA: marca, nueva conversación, historial y menú de usuario."""

from __future__ import annotations

import html

import streamlit as st

from src.ui import state
from src.ui.dialogs import delete_data_dialog, export_dialog
from src.ui.sidebar_threads import render_threads
from src.ui.theme import sidebar_brand
from src.utils.constants import ROLE_LABELS


def _initials(name: str) -> str:
    parts = [p for p in (name or "?").split() if p]
    return "".join(p[0] for p in parts[:2]).upper() or "?"


def _user_card() -> None:
    user = state.user() or {}
    name, role = (
        user.get("name") or user.get("username", ""),
        user.get("role", "operador"),
    )
    with (
        st.container(key="user_card"),
        st.popover(name, icon=":material/account_circle:", width="stretch"),
    ):
        st.html(
            f'<div class="hz-user-head"><div class="hz-avatar">{html.escape(_initials(name))}</div>'
            f"<div><b>{html.escape(name)}</b><span>@{html.escape(user.get('username', ''))} · "
            f"{ROLE_LABELS.get(role, role)}</span></div></div>"
        )
        if st.button(
            "Exportar conversación", icon=":material/download:", width="stretch"
        ):
            export_dialog()
        if st.button(
            "Eliminar mis datos", icon=":material/delete_forever:", width="stretch"
        ):
            delete_data_dialog()
        st.divider()
        if st.button(
            "Cerrar sesión", icon=":material/logout:", width="stretch", key="logout"
        ):
            state.logout()
            st.rerun()


def render_sidebar(full: bool = True) -> None:
    """full=False (dashboard): solo marca y menú de usuario."""
    with st.sidebar:
        sidebar_brand()
        if not full:
            _user_card()
            return
        if st.button(
            "Nueva conversación",
            icon=":material/edit_square:",
            key="new_chat",
            width="stretch",
        ):
            state.new_thread()
            st.rerun()
        render_threads()
        _user_card()
