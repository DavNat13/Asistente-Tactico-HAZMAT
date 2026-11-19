"""Restablecer la contraseña: 1) correo → respuesta uniforme; 2) código + nueva contraseña."""

from __future__ import annotations

import streamlit as st

from src.security.recovery import request_reset, reset_password
from src.ui.auth_common import (
    client_ip,
    go,
    notify,
    numeric_code_input,
    password_checks,
    title,
)
from src.ui.auth_errors import report


def _request() -> None:
    title(
        "key", "Recupera tu acceso", "Te enviaremos un código a tu correo verificado."
    )
    with st.form("reset_request", border=False):
        email = st.text_input(
            "Correo electrónico",
            placeholder="ej. camila@bomberos.cl",
            max_chars=120,
            autocomplete="email",
            icon=":material/mail:",
        )
        submitted = st.form_submit_button(
            "Enviar código", type="primary", icon=":material/send:", width="stretch"
        )
    if submitted:
        with st.spinner("Procesando…"):
            message = request_reset(email or "", ip=client_ip())
        notify(message, "info")  # siempre el mismo texto, exista o no la cuenta
        go("reset", stage="confirm", email=(email or "").strip().lower())


def _confirm(email: str) -> None:
    title(
        "key", "Crea una nueva contraseña", "Ingresa el código y tu nueva contraseña."
    )
    code = st.text_input(
        "Código de verificación",
        max_chars=6,
        placeholder="000000",
        autocomplete="one-time-code",
        icon=":material/pin:",
        validate=(r"^\d{6}$", "Ingresa los 6 dígitos del código"),
        key="reset_code",
    )
    numeric_code_input()
    pwd = {"type": "password", "max_chars": 128, "autocomplete": "new-password"}
    new = st.text_input(
        "Nueva contraseña",
        placeholder="Crea una contraseña segura",
        icon=":material/lock:",
        live=True,
        key="reset_new",
        **pwd,
    )
    confirm = st.text_input(
        "Confirmar contraseña",
        placeholder="Repite la nueva contraseña",
        icon=":material/lock_reset:",
        live=True,
        key="reset_confirm",
        **pwd,
    )
    password_checks(new or "", confirm or "")
    if st.button(
        "Cambiar contraseña", type="primary", icon=":material/check:", width="stretch"
    ):
        try:
            reset_password(email, code or "", new or "", confirm or "", ip=client_ip())
        except ValueError as e:
            st.error(str(e), icon=":material/error:")
            return
        except Exception as exc:  # noqa: BLE001
            st.error(report(exc, "cambiar contraseña"), icon=":material/error:")
            return
        notify("Contraseña actualizada. Ya puedes iniciar sesión.")
        go(None)
    if st.button("Pedir otro código", type="tertiary", icon=":material/refresh:"):
        go("reset", stage="request")


def reset_step(data: dict) -> None:
    if data.get("stage") == "confirm":
        _confirm(data.get("email", ""))
    else:
        _request()
    if st.button("Volver al inicio", type="tertiary", icon=":material/arrow_back:"):
        go(None)
