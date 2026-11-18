"""Formularios de inicio de sesión y registro (etiqueta + placeholder + ícono en cada campo)."""

from __future__ import annotations

import streamlit as st

from src.security.auth import MIN_PASSWORD, authenticate
from src.security.registration import register_user
from src.ui.icons import ACCENT, MUTED, icon


def _title(icon_name: str, title: str, subtitle: str) -> None:
    st.html(
        f'<div class="hz-auth-title"><div class="hz-badge">{icon(icon_name, ACCENT, 22)}</div>'
        f"<div><h3>{title}</h3><p>{subtitle}</p></div></div>"
    )


def _start_session(account: dict, welcome: str | None = None) -> None:
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.session_state.user = account
    if welcome:  # se muestra tras el rerun (un toast previo al rerun se perdería)
        st.session_state.flash = welcome
    st.rerun()


def login_form() -> None:
    _title("lock", "Inicia sesión", "Accede a tus conversaciones y consultas.")
    with st.form("login", border=False):
        login = st.text_input(
            "Usuario o correo",
            placeholder="ej. camila.rojas o camila@bomberos.cl",
            autocomplete="username",
            max_chars=120,
            icon=":material/person:",
        )
        password = st.text_input(
            "Contraseña",
            type="password",
            placeholder="Tu contraseña",
            autocomplete="current-password",
            max_chars=128,
            icon=":material/lock:",
        )
        submitted = st.form_submit_button(
            "Iniciar sesión", type="primary", icon=":material/login:", width="stretch"
        )
    if not submitted:
        return
    if not login or not password:
        st.warning("Completa usuario y contraseña.", icon=":material/info:")
        return
    try:
        account = authenticate(login, password)
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


def _requirements() -> None:
    ok = icon("check", MUTED, 13)
    st.html(
        f'<div class="hz-req"><span>{ok}Mínimo {MIN_PASSWORD} caracteres</span>'
        f"<span>{ok}Letras y números o símbolos</span></div>"
    )


def register_form() -> None:
    _title(
        "shield", "Crea tu cuenta", "Tus conversaciones quedan guardadas solo para ti."
    )
    with st.form("register", border=False):
        name = st.text_input(
            "Nombre completo",
            placeholder="ej. Camila Rojas",
            max_chars=60,
            icon=":material/badge:",
        )
        c1, c2 = st.columns(2)
        username = c1.text_input(
            "Usuario",
            placeholder="camila.rojas",
            max_chars=32,
            autocomplete="username",
            icon=":material/alternate_email:",
            help="3 a 32 caracteres: letras minúsculas, números, punto, guion o guion bajo.",
        )
        email = c2.text_input(
            "Correo electrónico",
            placeholder="camila@bomberos.cl",
            max_chars=120,
            autocomplete="email",
            icon=":material/mail:",
        )
        c3, c4 = st.columns(2)
        password = c3.text_input(
            "Contraseña",
            type="password",
            placeholder="Crea una contraseña",
            max_chars=128,
            autocomplete="new-password",
            icon=":material/lock:",
        )
        confirm = c4.text_input(
            "Confirmar contraseña",
            type="password",
            placeholder="Repite la contraseña",
            max_chars=128,
            autocomplete="new-password",
            icon=":material/lock_reset:",
        )
        _requirements()
        accepted = st.checkbox(
            "Acepto el aviso de privacidad y el uso como herramienta de apoyo"
        )
        submitted = st.form_submit_button(
            "Crear cuenta",
            type="primary",
            icon=":material/person_add:",
            width="stretch",
        )
    if not submitted:
        return
    try:
        account = register_user(username, name, email, password, confirm, accepted)
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
