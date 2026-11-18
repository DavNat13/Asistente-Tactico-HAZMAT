"""Diálogos de cuenta: exportar la conversación y eliminar los datos del usuario."""

from __future__ import annotations

import streamlit as st

from src.ui import state


@st.dialog("Exportar conversación", icon=":material/download:")
def export_dialog() -> None:
    mgr, sid, tid = (
        state.manager(),
        st.session_state.get("session_id"),
        st.session_state.get("thread_id"),
    )
    if not (mgr and sid and tid and st.session_state.get("history")):
        st.info(
            "Abre una conversación con mensajes para exportarla.",
            icon=":material/info:",
        )
        return
    st.caption("Descarga el historial de la conversación abierta.")
    c1, c2 = st.columns(2)
    for col, (fmt, label, mime, icon) in zip(
        (c1, c2),
        (
            ("markdown", "Markdown", "text/markdown", ":material/description:"),
            ("json", "JSON", "application/json", ":material/data_object:"),
        ),
        strict=True,
    ):
        data = mgr.export_chat_bytes(sid, tid, fmt)
        if data:
            col.download_button(
                label,
                data=data,
                file_name=data.name,
                mime=mime,
                icon=icon,
                width="stretch",
                key=f"dl_{fmt}",
            )


@st.dialog("Eliminar mis datos", icon=":material/delete_forever:")
def delete_data_dialog() -> None:
    st.write(
        "Se eliminarán **definitivamente** todas tus conversaciones. Esta acción no se puede deshacer. "
        "Las métricas de uso ya están seudonimizadas y no contienen tus mensajes."
    )
    confirm = st.text_input("Escribe ELIMINAR para confirmar", max_chars=10)
    if st.button(
        "Eliminar definitivamente",
        type="primary",
        width="stretch",
        disabled=confirm != "ELIMINAR",
    ):
        mgr, user = state.manager(), state.user() or {}
        try:
            n = mgr.delete_user_data(user["username"]) if mgr else 0
        except Exception:  # noqa: BLE001
            st.error("No se pudo completar la eliminación. Intenta más tarde.")
            return
        state.logout()
        st.session_state.user = user
        st.session_state.flash = f"Se eliminaron tus datos ({n} sesión/es)."
        st.rerun()
