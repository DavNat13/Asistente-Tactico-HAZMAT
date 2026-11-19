"""Formularios de inicio de sesión y registro (una columna, etiqueta + placeholder + ícono)."""

from __future__ import annotations

import streamlit as st

from src.security.auth import authenticate
from src.security.registration import PendingVerification, register_user
from src.ui.auth_common import client_ip, go, password_checks, route, title
from src.ui.privacy_dialog import acceptance


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


@st.fragment
def register_form() -> None:
    """Sin st.form: los checks de contraseña se actualizan mientras se escribe (`live`)."""
    title(
        "shield", "Crea tu cuenta", "Te enviaremos un código para verificar tu correo."
    )
    name = st.text_input(
        "Nombre completo",
        placeholder="ej. Camila Rojas",
        max_chars=60,
        icon=":material/badge:",
        key="reg_name",
    )
    username = st.text_input(
        "Usuario",
        placeholder="ej. camila.rojas",
        max_chars=32,
        autocomplete="username",
        icon=":material/alternate_email:",
        help="3 a 32 caracteres: letras minúsculas, números, punto, guion o guion bajo.",
        key="reg_user",
    )
    email = st.text_input(
        "Correo electrónico",
        placeholder="ej. camila@bomberos.cl",
        max_chars=120,
        autocomplete="email",
        icon=":material/mail:",
        key="reg_email",
    )
    pwd = {"type": "password", "max_chars": 128, "autocomplete": "new-password"}
    password = st.text_input(
        "Contraseña",
        placeholder="Crea una contraseña segura",
        icon=":material/lock:",
        live=True,
        key="reg_pass",
        **pwd,
    )
    confirm = st.text_input(
        "Confirmar contraseña",
        placeholder="Repite la contraseña",
        icon=":material/lock_reset:",
        live=True,
        key="reg_confirm",
        **pwd,
    )
    password_checks(password or "", confirm or "")
    accepted = acceptance("reg_accept")
    if not st.button(
        "Crear cuenta", type="primary", icon=":material/person_add:", width="stretch"
    ):
        return
    try:
        account = register_user(
            username, name, email, password, confirm, accepted, ip=client_ip()
        )
    except PendingVerification as e:
        st.info(str(e), icon=":material/mark_email_unread:")
        return
    except ValueError as e:
        st.error(str(e), icon=":material/error:")
        return
    except Exception:  # noqa: BLE001
        st.error(
            "No se pudo crear la cuenta. Intenta en unos minutos.",
            icon=":material/cloud_off:",
        )
        return
    go("verify", username=account["username"], email=account["email"], signup=True)
