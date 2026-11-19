"""Formulario de inicio de sesión (etiqueta + placeholder + ícono). El registro está en auth_register."""

from __future__ import annotations

import streamlit as st

from src.security.auth import authenticate
from src.ui.auth_common import (
    go,
    route,
    title,
)


def login_form() -> None:
    title("lock", "Inicia sesión", "Accede a tus conversaciones y consultas.")
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
    if st.button("¿Olvidaste tu contraseña?", type="tertiary", key="forgot"):
        go("reset", stage="request")
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
    route(account)
