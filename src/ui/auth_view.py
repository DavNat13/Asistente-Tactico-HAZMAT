"""Pantalla de inicio de sesión con aviso de privacidad."""

from __future__ import annotations

import html

import streamlit as st

from src.config.settings import settings
from src.utils.constants import APP_NAME, APP_SHORT

PRIVACY_NOTICE = (
    "Al ingresar aceptas que tus consultas se procesen para responderte. Los datos personales "
    "(RUT, teléfonos, correos, patentes) se ocultan automáticamente antes de enviarse al modelo de IA. "
    f"El historial se conserva {settings.SESSION_TTL_DAYS} días y puedes eliminarlo cuando quieras "
    "(Ley 19.628 y Ley 21.719). Herramienta de apoyo: no reemplaza al mando del incidente."
)


def render_login() -> None:
    st.html(
        '<div class="hz-login-head">'
        f'<div class="hz-mark">{html.escape(APP_SHORT)}</div>'
        f'<div class="hz-title">{html.escape(APP_NAME)}</div>'
        '<div class="hz-sub">Acceso para personal autorizado</div></div>'
    )
    _, col, _ = st.columns([1, 2, 1])
    with col, st.form("login", border=True):
        username = st.text_input("Usuario", autocomplete="username", max_chars=32)
        password = st.text_input(
            "Contraseña",
            type="password",
            autocomplete="current-password",
            max_chars=128,
        )
        submitted = st.form_submit_button("Ingresar", type="primary", width="stretch")
    if submitted:
        _login(username, password)
    with col:
        st.html(f'<p class="hz-legal">{html.escape(PRIVACY_NOTICE)}</p>')


def _login(username: str, password: str) -> None:
    from src.security.auth import authenticate

    try:
        account = authenticate(username, password)
    except Exception:  # noqa: BLE001 — BD caída: no revelar detalles
        st.error("El servicio de autenticación no está disponible. Intenta más tarde.")
        return
    if not account:
        st.error("Usuario o contraseña incorrectos, o cuenta bloqueada temporalmente.")
        return
    st.session_state.user = account
    st.rerun()
