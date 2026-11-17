"""Barra lateral: nueva conversación, historial, exportación y cuenta (privacidad)."""

from __future__ import annotations

import streamlit as st

from src.ui import state


def render_sidebar() -> None:
    with st.sidebar:
        if st.button(
            "Nueva conversación",
            icon=":material/edit_square:",
            width="stretch",
        ):
            state.new_thread()
            st.rerun()
        _history()
        st.html('<div class="hz-side-label">Cuenta</div>')
        _account()


def _history() -> None:
    threads = [t for t in state.threads() if t.message_count]
    st.html('<div class="hz-side-label">Recientes</div>')
    if not threads:
        st.caption("Aún no hay conversaciones.")
        return
    current = st.session_state.get("thread_id")
    for t in threads[:15]:
        active = t.thread_id == current
        if st.button(
            t.title,
            key=f"t_{t.thread_id}",
            icon=":material/chat_bubble:"
            if active
            else ":material/chat_bubble_outline:",
            type="secondary" if active else "tertiary",
            width="stretch",
        ):
            state.open_thread(t.thread_id)
            st.rerun()


def _account() -> None:
    user = state.user() or {}
    st.caption(f"{user.get('name', '')} · {user.get('role', '')}")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Exportar", icon=":material/download:", width="stretch"):
            _export_dialog()
    with c2:
        if st.button("Salir", icon=":material/logout:", width="stretch"):
            state.logout()
            st.rerun()
    if st.button(
        "Eliminar mis datos",
        icon=":material/delete:",
        type="tertiary",
        width="stretch",
    ):
        _delete_dialog()


@st.dialog("Exportar conversación")
def _export_dialog() -> None:
    mgr, sid, tid = (
        state.manager(),
        st.session_state.get("session_id"),
        st.session_state.get("thread_id"),
    )
    if not (mgr and sid and tid):
        st.info("No hay una conversación guardada para exportar.")
        return
    for fmt, label, mime in (
        ("markdown", "Markdown", "text/markdown"),
        ("json", "JSON", "application/json"),
    ):
        data = mgr.export_chat_bytes(sid, tid, fmt)
        if data:
            st.download_button(
                f"Descargar {label}",
                data=data,
                file_name=data.name,
                mime=mime,
                width="stretch",
                key=f"dl_{fmt}",
            )


@st.dialog("Eliminar mis datos")
def _delete_dialog() -> None:
    st.write(
        "Se eliminarán **definitivamente** todas tus conversaciones guardadas. "
        "Las métricas de uso ya están seudonimizadas y no contienen tus mensajes."
    )
    if st.button("Eliminar definitivamente", type="primary", width="stretch"):
        mgr, user = state.manager(), state.user() or {}
        try:
            n = mgr.delete_user_data(user["username"]) if mgr else 0
        except Exception:  # noqa: BLE001
            st.error("No se pudo completar la eliminación. Intenta más tarde.")
            return
        username, role = user.get("username"), user.get("role")
        state.logout()
        st.session_state.user = {"username": username, "name": username, "role": role}
        st.toast(f"Datos eliminados ({n} sesiones).", icon=":material/check:")
        st.rerun()
