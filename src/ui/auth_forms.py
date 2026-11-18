"""Formularios de inicio de sesión y registro."""

from __future__ import annotations

import streamlit as st

from src.security.auth import MIN_PASSWORD, authenticate
from src.security.registration import register_user


def _title(title: str, subtitle: str) -> None:
    st.html(f'<div class="hz-auth-title"><h3>{title}</h3><p>{subtitle}</p></div>')


def _start_session(account: dict, welcome: str | None = None) -> None:
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.session_state.user = account
    if welcome:  # se muestra tras el rerun (un toast previo al rerun se perdería)
        st.session_state.flash = welcome
    st.rerun()


def login_form() -> None:
    _title("Bienvenido de vuelta", "Ingresa con tu cuenta para continuar.")
    with st.form("login", border=False):
        username = st.text_input(
            "Usuario",
            placeholder="tu.usuario",
            autocomplete="username",
            max_chars=32,
            icon=":material/person:",
        )
        password = st.text_input(
            "Contraseña",
            type="password",
            autocomplete="current-password",
            max_chars=128,
            icon=":material/key:",
        )
        submitted = st.form_submit_button(
            "Iniciar sesión", type="primary", width="stretch"
        )
    if not submitted:
        return
    if not username or not password:
        st.warning("Completa usuario y contraseña.", icon=":material/info:")
        return
    try:
        account = authenticate(username, password)
    except Exception:  # noqa: BLE001 — no revelar detalles internos
        st.error(
            "El servicio no está disponible. Intenta en unos minutos.",
            icon=":material/cloud_off:",
        )
        return
    if not account:
        st.error(
            "Usuario o contraseña incorrectos, o cuenta bloqueada temporalmente.",
            icon=":material/error:",
        )
        return
    _start_session(account)


def register_form() -> None:
    _title("Crea tu cuenta", "Tus conversaciones quedan guardadas solo para ti.")
    with st.form("register", border=False):
        name = st.text_input(
            "Nombre",
            placeholder="Ej. Camila Rojas",
            max_chars=60,
            icon=":material/badge:",
        )
        username = st.text_input(
            "Usuario",
            placeholder="3 a 32 caracteres: letras, números, . _ -",
            max_chars=32,
            autocomplete="username",
            icon=":material/person:",
        )
        c1, c2 = st.columns(2)
        password = c1.text_input(
            "Contraseña",
            type="password",
            max_chars=128,
            autocomplete="new-password",
            help=f"Mínimo {MIN_PASSWORD} caracteres, combinando letras con números o símbolos.",
            icon=":material/key:",
        )
        confirm = c2.text_input(
            "Repetir contraseña",
            type="password",
            max_chars=128,
            autocomplete="new-password",
            icon=":material/key:",
        )
        accepted = st.checkbox(
            "Acepto el aviso de privacidad y el uso como herramienta de apoyo"
        )
        submitted = st.form_submit_button(
            "Crear cuenta", type="primary", width="stretch"
        )
    if not submitted:
        return
    try:
        account = register_user(username, name, password, confirm, accepted)
    except ValueError as e:
        st.error(str(e), icon=":material/error:")
        return
    except Exception:  # noqa: BLE001
        st.error(
            "No se pudo crear la cuenta. Intenta en unos minutos.",
            icon=":material/cloud_off:",
        )
        return
    _start_session(account, f"¡Cuenta creada! Bienvenido/a, {account['name']}.")
