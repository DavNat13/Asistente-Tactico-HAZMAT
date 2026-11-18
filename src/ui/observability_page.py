"""Dashboard de observabilidad (solo rol admin) — datos EN VIVO de MongoDB (`agent_runs`).

Por defecto muestra solo el uso real de la app (canal `ui`). Las corridas automáticas de evaluación
(canal `eval`) se ven aparte, rotuladas como tales, para no mezclar pruebas con uso productivo.
"""

from __future__ import annotations

from datetime import UTC, datetime

import streamlit as st

from src.observability import metrics as m
from src.observability import metrics_breakdown as mb
from src.ui import state
from src.ui.observability_improve import tab_improve
from src.ui.observability_records import tab_evals, tab_log
from src.ui.observability_tabs import tab_security, tab_usage
from src.ui.sidebar import render_sidebar

PERIODS = {
    "24 h": (1, "1h"),
    "7 días": (7, "6h"),
    "30 días": (30, "1D"),
    "90 días": (90, "1D"),
}
ORIGINS = {"Usuarios reales": "ui", "Pruebas automáticas": "eval", "Todo": None}


@st.cache_data(ttl=30, show_spinner="Consultando telemetría…")
def _load(days: int, channel: str | None):
    loaded_at = datetime.now(UTC).astimezone().strftime("%H:%M:%S")
    return (
        m.load_runs(days, channel),
        mb.security_events(days),
        mb.eval_runs(),
        loaded_at,
    )


def _header() -> tuple[int, str, str | None]:
    st.html('<div class="hz-dash"></div>')
    top = st.columns([3, 2], vertical_alignment="bottom")
    top[0].markdown("## :material/monitoring: Observabilidad")
    with top[1]:
        c1, c2 = st.columns([3, 1], vertical_alignment="bottom")
        period = c1.segmented_control(
            "Periodo", list(PERIODS), default="7 días", required=True, key="obs_period"
        )
        if c2.button(
            "", icon=":material/refresh:", help="Actualizar ahora", key="obs_refresh"
        ):
            _load.clear()
    origin = st.segmented_control(
        "Origen de los datos",
        list(ORIGINS),
        default="Usuarios reales",
        required=True,
        key="obs_origin",
    )
    days, freq = PERIODS[period]
    return days, freq, ORIGINS[origin]


def observability_page() -> None:
    if not state.is_admin():
        st.error("Acceso restringido a administradores.", icon=":material/lock:")
        st.stop()
    state.init_chat_state()
    render_sidebar(full=False)
    days, freq, channel = _header()
    try:
        runs, sec, evals, loaded_at = _load(days, channel)
    except Exception:  # noqa: BLE001
        st.error(
            "No se pudo leer la telemetría: la base de datos no responde.",
            icon=":material/cloud_off:",
        )
        return
    st.caption(
        f":green[●] Datos en vivo desde MongoDB · {len(runs)} ejecuciones en el periodo · "
        f"actualizado {loaded_at}"
    )
    usage, security, offline, improve, log = st.tabs(
        [
            ":material/insights: Uso real",
            ":material/shield: Seguridad",
            ":material/science: Evaluación offline",
            ":material/thumbs_up_down: Mejora continua",
            ":material/list_alt: Registro",
        ]
    )
    with usage:
        tab_usage(runs, freq)
    with security:
        tab_security(runs, sec)
    with offline:
        tab_evals(evals)
    with improve:
        tab_improve()
    with log:
        tab_log(runs)
