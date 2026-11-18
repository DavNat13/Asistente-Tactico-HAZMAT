"""Historial de conversaciones agrupado por fecha, con menú para renombrar o eliminar."""

from __future__ import annotations

from datetime import datetime

import streamlit as st

from src.ui import state

GROUPS = ("Hoy", "Ayer", "Últimos 7 días", "Últimos 30 días", "Anteriores")


def _group(updated: datetime, today) -> str:
    local = updated.astimezone() if updated.tzinfo else updated
    days = (today - local.date()).days
    if days <= 0:
        return GROUPS[0]
    if days == 1:
        return GROUPS[1]
    if days <= 7:
        return GROUPS[2]
    return GROUPS[3] if days <= 30 else GROUPS[4]


def grouped() -> list[tuple[str, list]]:
    threads = sorted(
        (t for t in state.threads() if t.message_count),
        key=lambda t: t.updated_at,
        reverse=True,
    )[:40]
    today = datetime.now().astimezone().date()
    buckets: dict[str, list] = {g: [] for g in GROUPS}
    for t in threads:
        buckets[_group(t.updated_at, today)].append(t)
    return [(g, ts) for g, ts in buckets.items() if ts]


def _row(t, active: bool) -> None:
    key = "thr_active" if active else f"thr_{t.thread_id}"
    with st.container(key=key, horizontal=True, vertical_alignment="center"):
        if st.button(t.title, key=f"open_{t.thread_id}", width="stretch", help=t.title):
            state.open_thread(t.thread_id)
            st.rerun()
        with st.popover("", icon=":material/more_horiz:", key=f"menu_{t.thread_id}"):
            title = st.text_input(
                "Renombrar", value=t.title, max_chars=80, key=f"title_{t.thread_id}"
            )
            if st.button(
                "Guardar nombre",
                icon=":material/edit:",
                key=f"ren_{t.thread_id}",
                width="stretch",
            ):
                state.rename_thread(t.thread_id, title)
                st.rerun()
            if st.button(
                "Eliminar conversación",
                icon=":material/delete:",
                key=f"del_{t.thread_id}",
                type="primary",
                width="stretch",
            ):
                state.delete_thread(t.thread_id)
                st.rerun()


def render_threads() -> None:
    groups = grouped()
    if not groups:
        st.caption("Tus conversaciones aparecerán aquí.")
        return
    current = st.session_state.get("thread_id")
    for label, threads in groups:
        st.html(f'<div class="hz-side-label">{label}</div>')
        for t in threads:
            _row(t, t.thread_id == current)
