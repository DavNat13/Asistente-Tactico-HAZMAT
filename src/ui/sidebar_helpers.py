import streamlit as st
from uuid import UUID


def _is_uuid(value) -> bool:
    try:
        UUID(str(value))
        return True
    except (ValueError, TypeError, AttributeError):
        return False


def switch_thread(mgr, sid, tid):
    if not (_is_uuid(sid) and _is_uuid(tid)):
        st.warning("Identificador de conversación inválido.")
        return False
    try:
        t = mgr.get_thread(sid, tid)
        if not t:
            return False
        st.session_state.thread_id = tid
        st.session_state.thread = t
        msgs = mgr.get_history(sid, tid)
        st.session_state.history = [
            {
                "role": m.role,
                "content": m.content,
                "sources": [
                    {"page": s.page, "source": s.source, "score": s.score}
                    for s in m.sources
                ]
                if m.sources
                else [],
            }
            for m in msgs
        ]
        st.rerun()
        return True
    except Exception:  # noqa: BLE001 — evita ConnectionResetError
        st.warning("No se pudo abrir la conversación.")
        return False


def create_thread(mgr, sid):
    if not _is_uuid(sid):
        st.warning("Sesión inválida.")
        return
    try:
        t = mgr.create_thread(sid)
        st.session_state.thread_id = t.thread_id
        st.session_state.thread = t
        st.session_state.history = []
        if "hist_radio" in st.session_state:  # deseleccionar el sentinel
            st.session_state.hist_radio = t.thread_id
        st.rerun()
    except Exception:  # noqa: BLE001
        st.warning("No se pudo crear la conversación.")


def reset_session():
    mgr = st.session_state.get("session_manager")
    if mgr:
        try:
            mgr.close()
        except Exception:  # noqa: BLE001
            pass
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()


def get_manager():
    return st.session_state.get("session_manager")


def get_sid():
    return st.session_state.get("session_id")


def get_tid():
    return st.session_state.get("thread_id")
