# sidebar_export.py — Modal de exportación con diseño moderno
import streamlit as st

from src.ui.sidebar_helpers import get_manager, get_sid, get_tid

_SEP = '<div style="border-top:1px solid rgba(245,242,233,.06);margin-top:.75rem;padding-top:.75rem"></div>'

_SVG_JSON = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/><path d="M10 12a1 1 0 0 0-1 1v1a1 1 0 0 1-1 1 1 1 0 0 1 1 1v1a1 1 0 0 0 1 1"/><path d="M14 18a1 1 0 0 0 1-1v-1a1 1 0 0 1 1-1 1 1 0 0 1-1-1v-1a1 1 0 0 0-1-1"/></svg>'
_SVG_MD = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="7 15 10 12 7 9"/><line x1="13" y1="15" x2="17" y2="15"/></svg>'


def render_exportar():
    st.markdown(_SEP, unsafe_allow_html=True)
    if st.button(
        ":material/file_download: Exportar conversaci\u00f3n",
        use_container_width=True,
        key="btn_export",
    ):
        _show_export_dialog()


@st.dialog("Exportar conversaci\u00f3n", width="large")
def _show_export_dialog():
    mgr, sid, tid = get_manager(), get_sid(), get_tid()
    if not (mgr and sid and tid):
        st.markdown(
            '<div class="export-title">Sin conversaci\u00f3n activa</div>'
            '<div class="export-subtitle">Inicia una consulta para poder exportarla.</div>',
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        f'<div class="export-title">Exportar conversaci\u00f3n</div>'
        f'<div class="export-subtitle">Elige el formato para descargar el historial de esta sesi\u00f3n.</div>'
        f'<div class="export-options">'
        f'<div class="export-option">'
        f'<div class="export-option-icon json">{_SVG_JSON}</div>'
        f'<div class="export-option-label">JSON</div>'
        f'<div class="export-option-desc">Estructura de datos. Ideal para integraciones y procesamiento autom\u00e1tico.</div>'
        f"</div>"
        f'<div class="export-option">'
        f'<div class="export-option-icon md">{_SVG_MD}</div>'
        f'<div class="export-option-label">Markdown</div>'
        f'<div class="export-option-desc">Formato legible. Perfecto para documentar y compartir con tu equipo.</div>'
        f"</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        d = mgr.export_chat_bytes(sid, tid, "json")
        if d:
            st.download_button(
                "\u2b07 Descargar JSON",
                data=d,
                file_name=d.name,
                mime="application/json",
                use_container_width=True,
                key="dl_json",
                type="secondary",
            )
    with c2:
        d = mgr.export_chat_bytes(sid, tid, "markdown")
        if d:
            st.download_button(
                "\u2b07 Descargar Markdown",
                data=d,
                file_name=d.name,
                mime="text/markdown",
                use_container_width=True,
                key="dl_md",
                type="secondary",
            )
