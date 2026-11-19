"""Panel de observabilidad (solo rol admin) — datos EN VIVO de MongoDB (`agent_runs`).

Por defecto muestra solo el uso real de la app (canal `ui`). Las corridas automáticas de evaluación
(canal `eval`) se ven aparte, rotuladas como tales, para no mezclar pruebas con uso productivo.
"""

from __future__ import annotations

from datetime import UTC, datetime

import streamlit as st

from src.observability import metrics as m
from src.observability import metrics_breakdown as mb
from src.observability.health_status import overall
from src.ui import state
from src.ui.observability_help import TABS_HELP, render_intro
from src.ui.observability_improve import tab_improve
from src.ui.observability_records import tab_evals, tab_log
from src.ui.observability_tabs import tab_security, tab_usage
from src.ui.sidebar import render_sidebar
from src.ui.ui_kit import page_header, status_banner

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


def _toolbar() -> tuple[int, str, str | None]:
    with st.container(key="obs_toolbar", horizontal=True, vertical_alignment="bottom"):
        period = st.segmented_control(
            "Periodo", list(PERIODS), default="7 días", required=True, key="obs_period"
        )
        origin = st.segmented_control(
            "Origen de los datos",
            list(ORIGINS),
            default="Usuarios reales",
            required=True,
            key="obs_origin",
        )
        if st.button(
            "Actualizar", icon=":material/refresh:", key="obs_refresh", type="tertiary"
        ):
            _load.clear()
    days, freq = PERIODS[period]
    return days, freq, ORIGINS[origin]


def observability_page() -> None:
    if not state.is_admin():
        st.error("Acceso restringido a administradores.", icon=":material/lock:")
        st.stop()
    state.init_chat_state()
    render_sidebar(full=False)
    st.html('<div class="hz-dash"></div>')
    page_header(
        "activity",
        "Observabilidad",
        "Cómo se está comportando el asistente con usuarios reales, en vivo.",
        kicker="Centro de mando",
    )
    days, freq, channel = _toolbar()
    try:
        runs, sec, evals, loaded_at = _load(days, channel)
    except Exception:  # noqa: BLE001
        status_banner(
            "crit",
            "No se pudo leer la telemetría",
            ["La base de datos no responde. Revisa MONGODB_URI y la conexión."],
        )
        return
    level, title, lines = overall(runs)
    status_banner(
        level,
        title,
        [*lines, f"{len(runs)} ejecuciones · actualizado {loaded_at}"],
    )
    render_intro()
    usage, security, offline, improve, log = st.tabs(
        [
            ":material/insights: Uso real",
            ":material/shield: Seguridad",
            ":material/science: Evaluación offline",
            ":material/thumbs_up_down: Mejora continua",
            ":material/list_alt: Registro",
        ]
    )
    for tab, key, render in (
        (usage, "usage", lambda: tab_usage(runs, freq)),
        (security, "security", lambda: tab_security(runs, sec)),
        (offline, "offline", lambda: tab_evals(evals)),
        (improve, "improve", tab_improve),
        (log, "log", lambda: tab_log(runs)),
    ):
        with tab:
            st.caption(TABS_HELP[key])
            render()
