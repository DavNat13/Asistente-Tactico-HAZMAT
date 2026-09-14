# sidebar_history.py — Renderizado de conversaciones recientes
import streamlit as st

from src.ui.sidebar_helpers import get_manager, get_sid, switch_thread

_EMPTY = '<p style="color:#F5F2E9;opacity:0.4;font-size:12px;padding:4px 8px">Sin conversaciones aún</p>'


def render_historial():
    st.markdown(
        '<div style="font-size:11px;font-weight:600;color:rgba(245,242,233,.5);'
        'letter-spacing:.03em;margin-bottom:.5rem;padding-left:8px">Conversaciones recientes</div>',
        unsafe_allow_html=True,
    )
    try:
        mgr, sid = get_manager(), get_sid()
        if not (mgr and sid):
            return st.markdown(_EMPTY, unsafe_allow_html=True)
        threads = mgr.get_active_threads(sid)
        if not threads:
            return st.markdown(_EMPTY, unsafe_allow_html=True)
        current_tid = st.session_state.get("thread_id")
        thread_ids = [t.thread_id for t in threads]
        titles = {t.thread_id: t.title for t in threads}
        default_idx = thread_ids.index(current_tid) if current_tid in thread_ids else 0

        def _fmt(tid):
            prefix = "\u25b8 " if tid == current_tid else "   "
            return f"{prefix}{titles[tid]}"

        def _on_change():
            sel = st.session_state.get("hist_radio")
            if sel and sel != current_tid:
                switch_thread(mgr, sid, sel)

        st.radio(
            "Historial",
            options=thread_ids,
            index=default_idx,
            format_func=_fmt,
            key="hist_radio",
            label_visibility="collapsed",
            on_change=_on_change,
        )
    except Exception:  # noqa: BLE001
        st.markdown(_EMPTY, unsafe_allow_html=True)
