"""Contenido de las pestañas del dashboard de observabilidad."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.observability import metrics as m
from src.observability import metrics_breakdown as mb
from src.ui import charts
from src.ui.kpis import render_kpis

EVAL_METRICS = [
    "keyword_score",
    "retrieval_hit",
    "citation_ok",
    "refusal_ok",
    "safe_output",
    "consistency",
]
EMPTY = "Aún no hay consultas en este periodo. Usa el chat y vuelve aquí: los datos aparecen en segundos."


def _section(title: str, caption: str = "") -> None:
    st.subheader(title, divider="gray")
    if caption:
        st.caption(caption)


def tab_usage(runs: pd.DataFrame, freq: str) -> None:
    if runs.empty:
        st.info(EMPTY, icon=":material/hourglass_empty:")
        return
    render_kpis(m.kpis(runs))
    _section(
        "Latencia en el tiempo",
        "Mediana (p50) y percentil 95 de las respuestas exitosas",
    )
    st.altair_chart(
        charts.latency_line(mb.latency_over_time(runs, freq)), width="stretch"
    )
    left, right = st.columns(2, gap="large")
    with left:
        _section("Tiempo medio por etapa", "Dónde se va el tiempo dentro del agente")
        st.altair_chart(
            charts.hbar(mb.node_breakdown(runs), "node", "ms", "ms", charts.NODE_NAMES),
            width="stretch",
        )
    with right:
        _section(
            "Latencia por nivel",
            "Bajo = sin LLM · Medio = RAG · Alto = plan de respuesta",
        )
        st.altair_chart(charts.level_bars(mb.by_level(runs)), width="stretch")
    _section("Errores por tipo")
    err = mb.errors(runs)
    if err.empty:
        st.success("Sin errores en el periodo.", icon=":material/check_circle:")
    else:
        st.altair_chart(
            charts.hbar(err, "error_type", "n", "ejecuciones", color=charts.CRITICAL),
            width="stretch",
        )


def tab_security(runs: pd.DataFrame, sec: pd.DataFrame) -> None:
    blocked = (
        runs[runs.get("blocked", pd.Series(dtype=bool)).map(lambda v: v is True)]
        if not runs.empty
        else runs
    )
    pii = int(runs["pii_redacted"].fillna(0).sum()) if "pii_redacted" in runs else 0
    c = st.columns(3)
    c[0].metric("Consultas bloqueadas", len(blocked))
    c[1].metric(
        "Datos personales ocultados",
        pii,
        help="RUT, teléfonos, correos y patentes redactados",
    )
    c[2].metric("Eventos de auditoría", int(sec["n"].sum()) if not sec.empty else 0)
    left, right = st.columns(2, gap="large")
    with left:
        _section("Bloqueos por categoría")
        reasons = mb.blocked_by_reason(runs)
        if reasons.empty:
            st.caption("Sin bloqueos en el periodo.")
        else:
            st.altair_chart(
                charts.hbar(
                    reasons, "reason", "n", "consultas", color=charts.SERIES[1]
                ),
                width="stretch",
            )
    with right:
        _section("Eventos de auditoría")
        if sec.empty:
            st.caption("Sin eventos en el periodo.")
        else:
            st.altair_chart(
                charts.hbar(sec, "kind", "n", "eventos", color=charts.SERIES[0]),
                width="stretch",
            )
