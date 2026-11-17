"""Dashboard de observabilidad (solo rol admin) — EV3 IE4."""

from __future__ import annotations

import streamlit as st

from src.observability import metrics as m
from src.observability import metrics_breakdown as mb
from src.ui import charts, state
from src.ui.charts_eval import eval_compare
from src.ui.kpis import render_kpis
from src.ui.theme import brand

PERIODS = {
    "Últimas 24 h": (1, "1h"),
    "Últimos 7 días": (7, "6h"),
    "Últimos 30 días": (30, "1D"),
}
CHANNELS = {"Usuarios": "ui", "Evaluaciones": "eval", "Todos": None}
EVAL_METRICS = [
    "keyword_score",
    "retrieval_hit",
    "citation_ok",
    "refusal_ok",
    "safe_output",
    "consistency",
]


@st.cache_data(ttl=60, show_spinner=False)
def _load(days: int, channel: str | None):
    return m.load_runs(days, channel), mb.security_events(days), mb.eval_runs()


def observability_page() -> None:
    if not state.is_admin():
        st.error("Acceso restringido.")
        st.stop()
    brand("Observabilidad del agente")
    c1, c2 = st.columns(2)
    period = c1.segmented_control("Periodo", list(PERIODS), default="Últimos 7 días")
    channel = c2.segmented_control("Origen", list(CHANNELS), default="Todos")
    days, freq = PERIODS[period or "Últimos 7 días"]
    try:
        runs, sec, evals = _load(days, CHANNELS[channel or "Todos"])
    except Exception:  # noqa: BLE001
        st.error("No se pudo leer la telemetría (base de datos no disponible).")
        return
    if runs.empty:
        st.info("Aún no hay ejecuciones registradas en este periodo.")
        return

    render_kpis(m.kpis(runs))
    st.subheader("Latencia en el tiempo", divider="gray")
    st.altair_chart(
        charts.latency_line(mb.latency_over_time(runs, freq)), width="stretch"
    )

    left, right = st.columns(2)
    with left:
        st.subheader("Tiempo medio por etapa", divider="gray")
        st.caption("Identifica el cuello de botella del grafo")
        st.altair_chart(
            charts.hbar(mb.node_breakdown(runs), "node", "ms", "ms", charts.NODE_NAMES),
            width="stretch",
        )
    with right:
        st.subheader("Latencia por nivel", divider="gray")
        st.caption("Bajo = sin LLM · Medio = RAG · Alto = agente con plan")
        st.altair_chart(charts.level_bars(mb.by_level(runs)), width="stretch")

    left, right = st.columns(2)
    with left:
        st.subheader("Errores por tipo", divider="gray")
        err = mb.errors(runs)
        if err.empty:
            st.success("Sin errores en el periodo.", icon=":material/check_circle:")
        else:
            st.altair_chart(
                charts.hbar(
                    err, "error_type", "n", "ejecuciones", color=charts.CRITICAL
                ),
                width="stretch",
            )
    with right:
        st.subheader("Eventos de seguridad", divider="gray")
        if sec.empty:
            st.caption("Sin eventos en el periodo.")
        else:
            st.altair_chart(
                charts.hbar(sec, "kind", "n", "eventos", color=charts.SERIES[1]),
                width="stretch",
            )

    if not evals.empty:
        st.subheader("Evaluación offline (antes vs. después)", divider="gray")
        st.altair_chart(eval_compare(evals, EVAL_METRICS), width="stretch")
        cols = [
            "label",
            "timestamp",
            "n_cases",
            "latency_p50_s",
            "latency_p95_s",
            "error_rate",
            *EVAL_METRICS,
        ]
        st.dataframe(
            evals[[c for c in cols if c in evals]],
            hide_index=True,
            width="stretch",
        )

    st.subheader("Ejecuciones con error o bloqueadas", divider="gray")
    bad = (
        runs[runs["status"] != "ok"].sort_values("created_at", ascending=False).head(50)
    )
    st.dataframe(
        bad[
            [
                "created_at",
                "status",
                "error_type",
                "block_reason",
                "complexity",
                "latency_s",
                "model",
                "run_id",
            ]
        ],
        hide_index=True,
        width="stretch",
    )
