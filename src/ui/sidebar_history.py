# sidebar_history.py — Renderizado de conversaciones recientes
from uuid import UUID

import streamlit as st

from src.ui.sidebar_helpers import create_thread, get_manager, get_sid, switch_thread

_EMPTY = '<p style="color:#F5F2E9;opacity:0.4;font-size:12px;padding:4px 8px">Sin conversaciones aún</p>'

_NEW_KEY = "__nueva_consulta__"
_NEW_LABEL = "▸ Nueva consulta..."


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

        def _fmt(key):
            if key == _NEW_KEY:
                return _NEW_LABEL
            prefix = "\u25b8 " if key == current_tid else "   "
            return f"{prefix}{titles.get(key, 'Conversación')}"

        # Mapa inverso: si el widget devuelve el texto legible, recuperar el UUID
        display_to_id = {_fmt(k): k for k in [_NEW_KEY] + thread_ids}
        display_to_id[_NEW_LABEL] = _NEW_KEY

        def _on_change():
            sel = st.session_state.get("hist_radio")
            try:
                if not sel or sel == current_tid:
                    return
                if sel in (_NEW_KEY, _NEW_LABEL):  # 1) interceptar sentinelas
                    return create_thread(mgr, sid)
                tid = display_to_id.get(sel, sel)  # 2) label → UUID
                UUID(tid)  # 3) validación dura
                switch_thread(mgr, sid, tid)
            except (ValueError, TypeError):  # 4) UI no se cae
                st.warning("Selección de conversación inválida.")
            except Exception:  # noqa: BLE001 — evita ConnectionResetError
                st.warning("No se pudo cambiar de conversación. Intente nuevamente.")

        st.radio(
            "Historial",
            options=[_NEW_KEY] + thread_ids,  # estado interno = claves reales
            index=default_idx + 1,  # +1 por el sentinel al inicio
            format_func=_fmt,  # usuario ve "▸ Nueva consulta..." / títulos
            key="hist_radio",
            label_visibility="collapsed",
            on_change=_on_change,
        )
    except Exception:  # noqa: BLE001
        st.markdown(_EMPTY, unsafe_allow_html=True)
