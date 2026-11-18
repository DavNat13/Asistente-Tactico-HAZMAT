"""Estado del incidente (checklist + bitácora) de la conversación abierta, persistido en el hilo."""

from __future__ import annotations

import logging

import streamlit as st

from src.agent.checklist import build_incident, toggle
from src.ui import state

log = logging.getLogger("hazmat.ui")


def current() -> dict | None:
    """Incidente del hilo actual (se lee de MongoDB una sola vez por hilo)."""
    tid = st.session_state.get("thread_id")
    if st.session_state.get("incident_tid") != tid:
        st.session_state.incident_tid = tid
        st.session_state.incident = None
        mgr, sid = state.manager(), st.session_state.get("session_id")
        if mgr and sid and tid:
            try:
                thread = mgr.get_thread(sid, tid)
                st.session_state.incident = thread.incident if thread else None
            except Exception as e:  # noqa: BLE001
                log.warning("No se pudo cargar el incidente: %s", type(e).__name__)
    return st.session_state.get("incident")


def _save(incident: dict | None) -> None:
    st.session_state.incident = incident
    mgr, sid, tid = (
        state.manager(),
        st.session_state.get("session_id"),
        st.session_state.get("thread_id"),
    )
    if mgr and sid and tid:
        try:
            mgr.set_incident(sid, tid, incident)
        except Exception as e:  # noqa: BLE001 — el checklist sigue funcionando en memoria
            log.warning("No se pudo guardar el incidente: %s", type(e).__name__)


def start(answer: str, un: str | None, title: str) -> None:
    _save(build_incident(answer, un, title))
    st.toast(
        "Checklist iniciado. El cronómetro está corriendo.", icon=":material/timer:"
    )


def mark(index: int, done: bool) -> None:
    incident = current()
    if incident:
        _save(toggle(incident, index, done))


def close() -> None:
    incident = current()
    if incident:
        from datetime import UTC, datetime

        now = datetime.now(UTC).isoformat()
        incident["closed_at"] = now
        incident["log"].append({"at": now, "text": "Cierre del incidente"})
        _save(incident)
