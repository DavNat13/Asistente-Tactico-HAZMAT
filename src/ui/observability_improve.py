"""Pestaña "Mejora continua": respuestas con 👎 → casos de evaluación aprobados por el admin."""

from __future__ import annotations

import streamlit as st

from src.observability import feedback
from src.ui import state
from src.ui.ui_kit import empty_state, stat_tile, tiles


def _candidate(c: dict) -> None:
    cid = c["_id"]
    with st.container(key=f"hzcard_cand_{cid}"):
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
    try:
        pending = feedback.list_candidates()
        approved = feedback.approved_cases()
    except Exception:  # noqa: BLE001
        empty_state("No se pudo leer la base de datos.", "alert")
        return
    tiles(
        [
            stat_tile(
                "Pendientes de revisión",
                f"{len(pending)}",
                "warn" if pending else "ok",
                "respuestas con 👎",
                "thumbs",
                "Respuestas que un usuario marcó como no útiles y esperan revisión.",
            ),
            stat_tile(
                "Casos aprobados",
                f"{len(approved)}",
                "info",
                "se suman a la evaluación nocturna",
                "check",
                "Casos que ya forman parte de las pruebas automáticas de cada noche.",
            ),
        ]
    )
    if not pending:
        empty_state("No hay respuestas pendientes de revisión.", "check")
    for c in pending:
        _candidate(c)
