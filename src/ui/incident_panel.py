"""Panel del incidente en curso: progreso, cronómetro en vivo y checklist por fases."""

from __future__ import annotations

from datetime import UTC, datetime
from itertools import groupby

import streamlit as st

from src.agent.checklist import progress
from src.ui import incident_state


def _elapsed(started_iso: str, closed_iso: str | None) -> str:
    start = datetime.fromisoformat(started_iso)
    end = datetime.fromisoformat(closed_iso) if closed_iso else datetime.now(UTC)
    secs = max(0, int((end - start).total_seconds()))
    h, rem = divmod(secs, 3600)
    return f"{h:02d}:{rem // 60:02d}:{rem % 60:02d}"


@st.fragment(run_every="1s")
def _clock(started: str, closed: str | None) -> None:
    st.metric("Tiempo transcurrido", _elapsed(started, closed), border=False)


def _toggle(index: int, key: str) -> None:
    incident_state.mark(index, bool(st.session_state.get(key)))


def render_incident_panel() -> None:
    incident = incident_state.current()
    if not incident:
        return
    done, total = progress(incident)
    closed = bool(incident.get("closed_at"))
    label = f"{incident['title']} · {done}/{total} pasos"
    with st.expander(
        label,
        icon=":material/task_alt:" if closed else ":material/emergency:",
        expanded=not closed,
    ):
        c1, c2 = st.columns([1, 2], vertical_alignment="center")
        with c1:
            _clock(incident["started_at"], incident.get("closed_at"))
        c2.progress(
            done / total if total else 0,
            text=f"Avance del checklist: {done} de {total}",
        )
        items = list(enumerate(incident["items"]))
        for phase, group in groupby(items, key=lambda x: x[1]["phase"]):
            st.markdown(f"**{phase}**")
            for idx, item in group:
                st.checkbox(
                    item["text"],
                    value=item["done"],
                    key=f"item_{st.session_state.get('thread_id')}_{idx}",
                    on_change=_toggle,
                    args=(idx, f"item_{st.session_state.get('thread_id')}_{idx}"),
                    disabled=closed,
                )
        with st.popover("Bitácora", icon=":material/history:"):
            for entry in reversed(incident["log"][-30:]):
                at = (
                    datetime.fromisoformat(entry["at"])
                    .astimezone()
                    .strftime("%H:%M:%S")
                )
                st.caption(f"**{at}** · {entry['text']}")
        if not closed and st.button(
            "Cerrar incidente", icon=":material/flag:", key="close_incident"
        ):
            incident_state.close()
            st.rerun()
