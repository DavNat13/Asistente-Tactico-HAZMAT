"""Registro en una columna con validación en vivo: cada campo muestra su error o confirmación y
"Crear cuenta" queda deshabilitado hasta que todo es válido y se acepta el aviso.
El backend repite las mismas validaciones (src/security/validators.py).
"""

from __future__ import annotations

from datetime import timedelta

import streamlit as st

from src.config.features import features
from src.security import otp
from src.security.registration import (
    MAIL_REQUIRED,
    PendingVerification,
    register_user,
)
from src.security.signup_failure import SignupError
from src.security.validators import (
    email_error,
    name_error,
    signup_errors,
    username_error,
)
from src.ui.auth_common import (
    client_ip,
    field_hint,
    go,
    password_checks,
    start_session,
    title,
)
from src.ui.auth_errors import local_now, report
from src.ui.privacy_dialog import acceptance

LIVE = "400ms"  # valida tras una pausa al escribir


@st.fragment
def register_form() -> None:
    """Sin st.form: los checks de contraseña se actualizan mientras se escribe (`live`)."""
    required = features.EMAIL_VERIFICATION_REQUIRED
    subtitle = (
        "Te enviaremos un código para verificar tu correo."
        if required
        else "Tu cuenta quedará activa al instante."
    )
    title("shield", "Crea tu cuenta", subtitle)
    top = st.container()  # todas las alertas del registro aparecen aquí, arriba
    blocked = required and not features.mail_enabled
    if blocked:
        top.warning(MAIL_REQUIRED, icon=":material/mail_lock:")
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
    ready = not errors and accepted and not blocked
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
        top.info(str(e), icon=":material/mark_email_unread:")
        top.button("Ir a Entrar", icon=":material/login:", on_click=_to_login)
        return
    except (
        ValueError,
        SignupError,
    ) as e:  # SignupError ya quedó registrado con su ref.
        top.error(str(e), icon=":material/error:")
        return
    except Exception as exc:  # noqa: BLE001 — se registra con traceback y referencia
        top.error(report(exc, "registro"), icon=":material/error:")
        return
    if account.get("requires") is None:  # verificación desactivada: entra directo
        start_session(account, f"¡Cuenta creada! Bienvenido/a, {account['name']}.")
    expires = local_now() + timedelta(minutes=otp.TTL_MINUTES["signup"])
    go(
        "verify",
        username=account["username"],
        email=account["email"],
        signup=True,
        expires=expires.strftime("%H:%M"),
    )


def _to_login() -> None:
    st.session_state["auth_mode"] = "Entrar"
