"""Render de mensajes del chat.

Seguridad (OWASP LLM05): el texto del modelo y del usuario se muestra con `st.markdown` SIN
`unsafe_allow_html`, por lo que cualquier HTML/JS que inyecte un ataque se muestra como texto.
Los únicos fragmentos HTML (chips) se construyen aquí con `html.escape`.
"""

from __future__ import annotations

import html

import streamlit as st

from src.observability.store import record_feedback
from src.security.text import strip_markup
from src.utils.constants import LEVEL_LABELS

AVATARS = {"user": ":material/person:", "assistant": ":material/local_fire_department:"}


def sources_from_docs(docs: list[dict], limit: int = 6) -> list[dict]:
    """Fuentes únicas (documento + página impresa), ordenadas por relevancia."""
    best: dict[tuple, dict] = {}
    for d in docs:
        md = d.get("metadata", {})
        page = str(md.get("page_label") or md.get("page_number") or "")
        key = (md.get("source", "GRE 2024"), page)
        score = float(d.get("score") or 0)
        if page and (key not in best or score > best[key]["score"]):
            best[key] = {"source": key[0], "page": page, "score": round(score, 3)}
    return sorted(best.values(), key=lambda s: s["score"], reverse=True)[:limit]


def meta_html(level: str | None, sources: list[dict], latency_ms: float | None) -> str:
    chips = []
    if level in LEVEL_LABELS:
        chips.append(
            f'<span class="hz-chip hz-level-{level}"><span class="hz-dot"></span>'
            f"{html.escape(LEVEL_LABELS[level])}</span>"
        )
    for s in sources:
        chips.append(
            f'<span class="hz-chip">{html.escape(str(s["source"]))} · '
            f"<b>p. {html.escape(str(s['page']))}</b></span>"
        )
    if latency_ms:
        chips.append(f'<span class="hz-chip">{latency_ms / 1000:.1f} s</span>')
    return f'<div class="hz-meta">{"".join(chips)}</div>' if chips else ""


def _feedback(run_id: str) -> None:
    key = f"fb_{run_id}"

    def _save():
        value = st.session_state.get(key)
        if value is not None:
            user = st.session_state.get("user") or {}
            record_feedback(run_id, 1 if value == 1 else -1, user.get("username"))

    st.feedback("thumbs", key=key, on_change=_save)


def render_message(msg: dict) -> None:
    role = msg.get("role", "assistant")
    with st.chat_message(role, avatar=AVATARS.get(role)):
        st.markdown(
            strip_markup(msg.get("content", ""))
        )  # historiales antiguos incluidos
        if role == "assistant":
            meta = meta_html(msg.get("complexity"), msg.get("sources", []), None)
            if meta:
                st.html(meta)
            if msg.get("run_id"):
                _feedback(msg["run_id"])
