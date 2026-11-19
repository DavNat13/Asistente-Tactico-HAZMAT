"""Piezas comunes de la pantalla de acceso: títulos, flujo pendiente, IP, avisos y checks de contraseña."""

from __future__ import annotations

import html

import streamlit as st

from src.security import verification
from src.security.passwords import MIN_PASSWORD
from src.ui.icons import ACCENT, icon

FLOW = "auth_flow"
NOTICE = "auth_notice"
OK_COLOR = "#16a34a"
PENDING_COLOR = "#78716c"
# Teclado numérico en móviles para los campos de código (constante del proyecto, sin datos del usuario)
_NUMERIC_JS = (
    "<script>(()=>{let n=0;const t=setInterval(()=>{document.querySelectorAll("
    "'.st-key-otp_code input,.st-key-reset_code input').forEach(e=>{"
    "e.setAttribute('inputmode','numeric');e.setAttribute('autocomplete','one-time-code')});"
    "if(++n>20)clearInterval(t)},150)})();</script>"
)


def title(icon_name: str, text: str, subtitle: str) -> None:
    st.html(
        f'<div class="hz-auth-title"><div class="hz-badge">{icon(icon_name, ACCENT, 22)}</div>'
        f"<div><h3>{text}</h3><p>{subtitle}</p></div></div>"
    )


def client_ip() -> str | None:
    """IP del cliente si Streamlit la expone (None en localhost o si no está disponible)."""
    try:
        return st.context.ip_address
    except Exception:  # noqa: BLE001 — versiones sin st.context.ip_address
        return None


def flow() -> dict | None:
    return st.session_state.get(FLOW)


def go(step: str | None, **data) -> None:
    """Cambia de paso (verify, email, privacy, reset) o vuelve a las pestañas con None."""
    if step is None:
        st.session_state.pop(FLOW, None)
    else:
        st.session_state[FLOW] = {"step": step, **data}
    st.rerun()


def notify(message: str, kind: str = "success") -> None:
    st.session_state[NOTICE] = (kind, message)


def show_notice() -> None:
    kind, message = st.session_state.pop(NOTICE, (None, None))
    if message:
        getattr(st, kind)(message, icon=":material/info:")


def start_session(account: dict, welcome: str | None = None) -> None:
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    account = {k: v for k, v in account.items() if k != "requires"}
    st.session_state.user = account
    if welcome:  # se muestra tras el rerun (un toast previo al rerun se perdería)
        st.session_state.flash = welcome
    st.rerun()


def mask_email(email: str | None) -> str:
    if not email or "@" not in email:
        return "tu correo"
    local, domain = email.split("@", 1)
    return f"{local[:1]}•••@{domain}"


def numeric_code_input() -> None:
    st.html(_NUMERIC_JS, unsafe_allow_javascript=True)


def password_checks(password: str, confirm: str | None = None) -> bool:
    """Lista de requisitos que se pone en verde a medida que se cumplen."""
    rules = [
        (len(password) >= MIN_PASSWORD, f"Mínimo {MIN_PASSWORD} caracteres"),
        (
            bool(password) and not (password.isalpha() or password.isdigit()),
            "Letras y números o símbolos",
        ),
    ]
    if confirm is not None:
        rules.append(
            (bool(password) and password == confirm, "Las contraseñas coinciden")
        )
    items = "".join(
        f'<span class="{"ok" if ok else ""}" role="listitem">'
        f"{icon('check' if ok else 'circle', OK_COLOR if ok else PENDING_COLOR, 14)}"
        f'{html.escape(label)}<span class="hz-sr">{" (cumplido)" if ok else ""}</span></span>'
        for ok, label in rules
    )
    st.html(f'<div class="hz-req" role="list" aria-live="polite">{items}</div>')
    return all(ok for ok, _ in rules)


def route(account: dict, welcome: str | None = None) -> None:
    """Inicia sesión o lleva al paso pendiente (verificar, agregar correo o reaceptar el aviso)."""
    step, user = account.get("requires"), account["username"]
    if step is None:
        start_session(account, welcome)
    elif step == "verify":
        try:
            sent = verification.ensure_code(user)
        except ValueError:  # espera de reenvío vigente: ya hay un código en camino
            sent = True
        notify(
            "Debes verificar tu correo para ingresar."
            + ("" if sent else " No pudimos enviar el código. Intenta reenviarlo."),
            "warning",
        )
        go("verify", username=user, email=account.get("email"), signup=False)
    elif step == "email":
        go("email", username=user)
    else:
        go("privacy", account=account)
