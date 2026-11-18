"""Estado de la sesión de Streamlit ligado al usuario autenticado.

La sesión de chat se resuelve SIEMPRE desde el usuario logueado en el servidor; nunca se acepta un
`session_id` desde la URL (eso permitía leer historiales ajenos — IDOR).
"""

from __future__ import annotations

import logging

import streamlit as st

from src.session.manager import SessionManager

log = logging.getLogger("hazmat.ui")


def user() -> dict | None:
    return st.session_state.get("user")


def is_admin() -> bool:
    u = user()
    return bool(u and u.get("role") == "admin")


def manager() -> SessionManager | None:
    return st.session_state.get("session_manager")


def _to_history(messages) -> list[dict]:
    return [
        {
            "role": m.role,
            "content": m.content,
            "sources": [
                {"page": s.page, "source": s.source, "score": s.score}
                for s in m.sources
            ],
        }
        for m in messages
    ]


def init_chat_state() -> None:
    """Carga (una vez por sesión del navegador) la sesión, el hilo activo y su historial."""
    st.session_state.setdefault("history", [])
    if "session_id" in st.session_state or not user():
        return
    try:
        mgr = SessionManager()
        session = mgr.get_or_create_user_session(user()["username"])
        threads = session.get_active_threads()
        thread = threads[-1] if threads else mgr.create_thread(session.session_id)
        st.session_state.session_manager = mgr
        st.session_state.session_id = session.session_id
        st.session_state.thread_id = thread.thread_id
        st.session_state.history = _to_history(
            mgr.get_history(session.session_id, thread.thread_id)
        )
    except Exception as e:  # noqa: BLE001 — sin BD el chat funciona, solo sin persistencia
        log.warning("Persistencia no disponible: %s", type(e).__name__)
        st.session_state.session_id = None
        st.session_state.thread_id = None


def threads() -> list:
    mgr, sid = manager(), st.session_state.get("session_id")
    if not (mgr and sid):
        return []
    try:
        return list(reversed(mgr.get_active_threads(sid)))
    except Exception:  # noqa: BLE001
        return []


def new_thread() -> None:
    mgr, sid = manager(), st.session_state.get("session_id")
    st.session_state.history = []
    if mgr and sid:
        try:
            st.session_state.thread_id = mgr.create_thread(sid).thread_id
        except Exception:  # noqa: BLE001
            st.toast("No se pudo crear la conversación.", icon=":material/error:")


def open_thread(thread_id: str) -> None:
    """Solo abre hilos que pertenecen a la sesión del usuario actual (filtrado por session_id)."""
    mgr, sid = manager(), st.session_state.get("session_id")
    if not (mgr and sid) or not mgr.get_thread(sid, thread_id):
        st.toast("Conversación no disponible.", icon=":material/error:")
        return
    st.session_state.thread_id = thread_id
    st.session_state.history = _to_history(mgr.get_history(sid, thread_id))


def rename_thread(thread_id: str, title: str) -> None:
    mgr, sid = manager(), st.session_state.get("session_id")
    title = (title or "").strip()[:80]
    if mgr and sid and title:
        try:
            mgr.rename_thread(sid, thread_id, title)
        except Exception:  # noqa: BLE001
            st.toast("No se pudo renombrar.", icon=":material/error:")


def delete_thread(thread_id: str) -> None:
    mgr, sid = manager(), st.session_state.get("session_id")
    if not (mgr and sid):
        return
    try:
        mgr.delete_thread(sid, thread_id)
    except Exception:  # noqa: BLE001
        st.toast("No se pudo eliminar.", icon=":material/error:")
        return
    if st.session_state.get("thread_id") == thread_id:
        new_thread()
    st.toast("Conversación eliminada.", icon=":material/delete:")


def logout() -> None:
    for key in list(st.session_state.keys()):
        del st.session_state[key]
