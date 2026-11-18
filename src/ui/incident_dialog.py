"""Diálogo "Ficha de incidente": vista previa, descarga en PDF y envío por correo con confirmación."""

from __future__ import annotations

import streamlit as st

from src.agent.zones import zones_for
from src.config.features import features
from src.reports.incident_pdf import build_incident_pdf
from src.security.accounts import normalize_email
from src.ui import incident_state, state


def _pdf(msg: dict, un: str | None, title: str) -> tuple[bytes, dict | None]:
    user = state.user() or {}
    z = zones_for(un, "pequeño") if un else None
    data = {
        "title": title,
        "user": user.get("name", ""),
        "answer": msg.get("content", ""),
        "sources": msg.get("sources", []),
        "zones": z.as_dict() if z else None,
        "incident": incident_state.current(),
    }
    return build_incident_pdf(data), data["zones"]


def _send(pdf: bytes, title: str, summary: str) -> None:
    from src.notify.notifications import mail_quota_left, send_incident_report

    user = state.user() or {}
    st.markdown("**Enviar por correo**")
    if not features.mail_enabled:
        st.info(
            "El envío de correos no está configurado en este servidor.",
            icon=":material/mail_lock:",
        )
        return
    to = st.text_input(
        "Destinatario",
        value=user.get("email") or "",
        placeholder="nombre@bomberos.cl",
        icon=":material/mail:",
        key="ficha_to",
    )
    confirm = st.checkbox(
        f"Confirmo que quiero enviar esta ficha a {to or '…'}", key="ficha_ok"
    )
    if st.button(
        "Enviar ficha",
        icon=":material/send:",
        type="primary",
        disabled=not confirm,
        width="stretch",
    ):
        try:
            to = normalize_email(to)
        except ValueError as e:
            st.error(str(e), icon=":material/error:")
            return
        if mail_quota_left(user.get("username", "")) <= 0:
            st.warning(
                "Alcanzaste el límite de envíos por hora. Intenta más tarde.",
                icon=":material/schedule:",
            )
            return
        with st.spinner("Enviando…"):
            ok = send_incident_report(user.get("username", ""), to, title, summary, pdf)
        if ok:
            st.success(f"Ficha enviada a {to}.", icon=":material/mark_email_read:")
        else:
            st.error(
                "No se pudo enviar el correo. Intenta nuevamente.",
                icon=":material/error:",
            )


@st.dialog("Ficha de incidente", icon=":material/description:", width="medium")
def incident_dialog(msg: dict, un: str | None) -> None:
    default = f"Incidente UN {un}" if un else "Incidente HAZMAT"
    title = st.text_input(
        "Título de la ficha", value=default, max_chars=90, icon=":material/title:"
    )
    pdf, z = _pdf(msg, un, title)
    if z:
        st.caption(
            f"Incluye distancias de la GRE (p. {z['page']}), el plan, el checklist y la bitácora si existen."
        )
    st.download_button(
        "Descargar PDF",
        data=pdf,
        file_name="ficha_incidente_hazmat.pdf",
        mime="application/pdf",
        icon=":material/download:",
        type="primary",
        width="stretch",
    )
    st.divider()
    summary = " ".join(msg.get("content", "").split())[:600]
    _send(pdf, title, summary)
