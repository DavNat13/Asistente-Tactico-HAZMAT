"""Flujo del chat: entrada → agente (streaming) → render seguro → persistencia."""

from __future__ import annotations

import logging

import streamlit as st

from src.agent.service import stream_query
from src.security.pii import redact
from src.security.text import strip_markup
from src.ui import state
from src.ui.message import AVATARS, meta_html, render_message, sources_from_docs

log = logging.getLogger("hazmat.ui")


def render_history() -> None:
    for msg in st.session_state.get("history", []):
        render_message(msg)


def _persist(role: str, content: str, sources: list[dict] | None = None) -> None:
    mgr, sid, tid = (
        state.manager(),
        st.session_state.get("session_id"),
        st.session_state.get("thread_id"),
    )
    if not (mgr and sid and tid and content):
        return
    try:
        if role == "user":
            mgr.add_user_message(sid, tid, content)
        else:
            rows = [
                {
                    "page": int(s["page"]) if str(s["page"]).isdigit() else 0,
                    "source": s["source"],
                    "score": min(max(s["score"], 0.0), 1.0),
                }
                for s in sources or []
            ]
            mgr.add_assistant_message(
                sid, tid, content, sources=rows, context_used=len(rows)
            )
    except Exception as e:  # noqa: BLE001 — no perder la respuesta si falla la BD
        log.warning("No se pudo guardar el mensaje: %s", type(e).__name__)


def ask(query: str) -> None:
    user = state.user() or {}
    clean, _ = redact(
        strip_markup(query)
    )  # nunca código ni datos personales en pantalla o BD
    if not clean:
        st.toast(
            "La consulta solo contenía código y fue descartada.",
            icon=":material/block:",
        )
        return
    prior = [
        {"role": m["role"], "content": m["content"]} for m in st.session_state.history
    ]
    st.session_state.history.append({"role": "user", "content": clean})
    _persist("user", clean)
    render_message({"role": "user", "content": clean})

    with st.chat_message("assistant", avatar=AVATARS["assistant"]):
        status = st.status("Analizando consulta…", expanded=False)
        placeholder = st.empty()
        text, final = "", {}
        for event in stream_query(
            query,
            thread_id=st.session_state.get("thread_id"),
            user_id=user.get("username"),
            history=prior,
        ):
            if event["type"] == "status":
                status.update(label=event["label"])
            elif event["type"] == "token":
                text += event["text"]
                placeholder.markdown(text + " ▌")
            else:
                final = event
        answer = final.get("answer") or "No se obtuvo respuesta. Intenta nuevamente."
        placeholder.markdown(answer)
        sources = sources_from_docs(final.get("chunks", []))
        if final.get("blocked"):
            status.update(label="Consulta no permitida", state="error")
        else:
            secs = (final.get("latency_ms") or 0) / 1000
            status.update(
                label=f"Respuesta verificada · {secs:.1f} s", state="complete"
            )
        meta = meta_html(final.get("complexity"), sources, final.get("latency_ms"))
        if meta:
            st.html(meta)

    st.session_state.history.append(
        {
            "role": "assistant",
            "content": answer,
            "sources": sources,
            "complexity": final.get("complexity"),
            "run_id": final.get("run_id"),
        }
    )
    _persist("assistant", answer, sources)
    st.rerun()  # re-render para mostrar el feedback del último mensaje
