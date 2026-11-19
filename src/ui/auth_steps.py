"""Pasos previos a entrar: verificar el correo, agregar un correo (cuentas antiguas) y reaceptar el aviso."""

from __future__ import annotations

import streamlit as st

from src.security import otp, privacy, verification
from src.security.auth import account_status
from src.ui.auth_common import go, mask_email, notify, numeric_code_input, route, title
from src.ui.privacy_dialog import acceptance, privacy_dialog


@st.fragment(run_every=1)
def _resend(username: str) -> None:
    """Temporizador de reenvío (se actualiza cada segundo solo en esta pantalla)."""
    left = otp.cooldown_left(username, "signup")
    label = f"Reenviar código en {left} s" if left else "Reenviar código"
    if st.button(
        label, type="tertiary", icon=":material/refresh:", disabled=bool(left)
    ):
        try:
            ok = verification.resend(username)
        except ValueError as e:
            st.warning(str(e), icon=":material/timer:")
            return
        if ok:
            st.toast("Te enviamos un código nuevo.", icon=":material/mark_email_read:")
        else:
            st.error("No pudimos enviar el código de verificación. Intenta más tarde")


def verify_step(data: dict) -> None:
    title("mail", "Revisa tu correo", "Ingresa el código para activar tu cuenta.")
    st.markdown(
        f"Enviamos un código de 6 dígitos a **{mask_email(data.get('email'))}**. "
        "Vence en 15 minutos y sirve una sola vez."
    )
    with st.form("otp", border=False):
        code = st.text_input(
            "Código de verificación",
            max_chars=6,
            placeholder="000000",
            autocomplete="one-time-code",
            icon=":material/pin:",
            validate=(r"^\d{6}$", "Ingresa los 6 dígitos del código"),
            key="otp_code",
        )
        submitted = st.form_submit_button(
            "Verificar y continuar",
            type="primary",
            icon=":material/verified:",
            width="stretch",
        )
    numeric_code_input()
    if submitted:
        account = verification.confirm(data["username"], code)
        if not account:
            st.error(
                "Código incorrecto o expirado. Tras 5 intentos fallidos debes pedir uno nuevo.",
                icon=":material/error:",
            )
        else:
            status = account_status(data["username"]) or {**account, "requires": None}
            hello = f"¡Correo verificado! Bienvenido/a, {account['name']}."
            route(status, hello if data.get("signup") else None)
    _resend(data["username"])
    c1, c2 = st.columns(2)
    if c1.button("Cambiar correo", type="tertiary", icon=":material/edit:"):
        if data.get("signup"):
            verification.cancel_pending(data["username"])
            notify("Registro anulado. Puedes registrarte con otro correo.", "info")
            go(None)
        go("email", username=data["username"])
    if c2.button("Volver al inicio", type="tertiary", icon=":material/arrow_back:"):
        go(None)


def email_step(data: dict) -> None:
    title("mail", "Agrega tu correo", "Lo usaremos para verificar tu cuenta.")
    with st.form("add_email", border=False):
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
    if st.button("Volver al inicio", type="tertiary", icon=":material/arrow_back:"):
        go(None)
    if not submitted:
        return
    try:
        sent = verification.set_email(data["username"], email)
    except ValueError as e:
        st.error(str(e), icon=":material/error:")
        return
    if not sent:
        st.error("No pudimos enviar el código de verificación. Intenta más tarde")
        return
    go("verify", username=data["username"], email=email.strip().lower(), signup=False)


def privacy_step(data: dict) -> None:
    title(
        "shield",
        "Actualizamos el aviso de privacidad",
        "Léelo y acéptalo para continuar.",
    )
    st.markdown(
        f"La versión vigente es **{privacy.PRIVACY_VERSION}**. Ábrelo, revisa los cambios y "
        "pulsa «He leído el aviso» para habilitar la aceptación."
    )
    if st.button(
        "Leer el aviso completo", icon=":material/description:", key="reaccept_read"
    ):
        privacy_dialog()
    accepted = acceptance("reaccept")
    if st.button(
        "Aceptar y continuar", type="primary", width="stretch", disabled=not accepted
    ):
        account = data["account"]
        privacy.accept(account["username"])
        route({**account, "requires": None})
    if st.button("Volver al inicio", type="tertiary", icon=":material/arrow_back:"):
        go(None)
