"""Pestaña "Mejora continua": respuestas con 👎 → casos de evaluación aprobados por el admin."""

from __future__ import annotations

import streamlit as st

from src.observability import feedback
from src.ui import state


def _candidate(c: dict) -> None:
    cid = c["_id"]
    with st.container(border=True, key=f"cand_{cid}"):
        st.markdown(f"**Pregunta:** {c['question']}")
        with st.expander("Respuesta que recibió 👎"):
            st.markdown(c.get("answer", ""))
        k1, k2 = st.columns([2, 1])
        kw = k1.text_input(
            "Datos clave esperados (separados por coma)",
            placeholder="ej. 128, 50 m",
            key=f"kw_{cid}",
            icon=":material/key:",
        )
        pages = k2.text_input(
            "Páginas GRE esperadas",
            placeholder="ej. 190",
            key=f"pg_{cid}",
            icon=":material/menu_book:",
        )
        b1, b2 = st.columns(2)
        if b1.button(
            "Aprobar como caso de evaluación",
            icon=":material/add_task:",
            key=f"ok_{cid}",
            type="primary",
            width="stretch",
        ):
            try:
                case = feedback.approve(
                    cid, kw, pages, (state.user() or {}).get("username", "")
                )
                st.toast(
                    f"Caso {case['_id']} agregado al set de evaluación.",
                    icon=":material/check_circle:",
                )
                st.rerun()
            except ValueError as e:
                st.error(str(e), icon=":material/error:")
        if b2.button(
            "Descartar", icon=":material/close:", key=f"no_{cid}", width="stretch"
        ):
            feedback.reject(cid)
            st.rerun()


def tab_improve() -> None:
    st.caption(
        "Cada respuesta marcada con 👎 llega aquí. Define qué datos debía contener y apruébala: se "
        "sumará a la evaluación nocturna (`--include-db-cases`) para que el error no se repita."
    )
    try:
        pending = feedback.list_candidates()
        approved = feedback.approved_cases()
    except Exception:  # noqa: BLE001
        st.error("No se pudo leer la base de datos.", icon=":material/cloud_off:")
        return
    c1, c2 = st.columns(2)
    c1.metric("Pendientes de revisión", len(pending))
    c2.metric("Casos aprobados desde feedback", len(approved))
    if not pending:
        st.success(
            "No hay respuestas pendientes de revisión.", icon=":material/check_circle:"
        )
    for c in pending:
        _candidate(c)
