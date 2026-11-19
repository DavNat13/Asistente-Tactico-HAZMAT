"""Registro en una columna con validación en vivo: cada campo muestra su error o confirmación y
"Crear cuenta" queda deshabilitado hasta que todo es válido y se acepta el aviso.
El backend repite las mismas validaciones (src/security/validators.py).
"""

from __future__ import annotations

import streamlit as st

from src.security.registration import PendingVerification, register_user
from src.security.validators import (
    email_error,
    name_error,
    signup_errors,
    username_error,
)
from src.ui.auth_common import client_ip, field_hint, go, password_checks, title
from src.ui.privacy_dialog import acceptance

LIVE = "400ms"  # valida tras una pausa al escribir


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
        live=LIVE,
        key="reg_name",
    )
    field_hint(name_error(name), name)
    username = st.text_input(
        "Usuario",
        placeholder="ej. camila.rojas",
        max_chars=32,
        autocomplete="username",
        icon=":material/alternate_email:",
        help="3 a 32 caracteres: letras, números, punto, guion o guion bajo. Se guarda en minúsculas.",
        live=LIVE,
        key="reg_user",
    )
    field_hint(username_error(username), username)
    email = st.text_input(
        "Correo electrónico",
        placeholder="ej. camila@bomberos.cl",
        max_chars=120,
        autocomplete="email",
        icon=":material/mail:",
        live=LIVE,
        key="reg_email",
    )
    field_hint(email_error(email), email)
    pwd = {"type": "password", "max_chars": 128, "autocomplete": "new-password"}
    password = st.text_input(
        "Contraseña",
        placeholder="Crea una contraseña segura",
        icon=":material/lock:",
        live=LIVE,
        key="reg_pass",
        **pwd,
    )
    confirm = st.text_input(
        "Confirmar contraseña",
        placeholder="Repite la contraseña",
        icon=":material/lock_reset:",
        live=LIVE,
        key="reg_confirm",
        **pwd,
    )
    password_checks(password or "", confirm or "")
    accepted = acceptance("reg_accept")
    errors = signup_errors(name, username, email, password, confirm)
    ready = not errors and accepted
    clicked = st.button(
        "Crear cuenta",
        type="primary",
        icon=":material/person_add:",
        width="stretch",
        disabled=not ready,
        help=None
        if ready
        else "Completa correctamente todos los campos y acepta el aviso",
    )
    if not ready:
        missing = len(errors) + (0 if accepted else 1)
        st.caption(f"Faltan {missing} paso(s): revisa los campos marcados en rojo.")
    if not clicked:
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
