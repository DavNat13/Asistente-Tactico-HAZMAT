"""Tarjetas de KPIs del dashboard."""

from __future__ import annotations

import pandas as pd
import streamlit as st


def _fmt(v, kind: str = "s") -> str:
    if v is None or pd.isna(v):
        return "—"
    return {"s": f"{v:.1f} s", "%": f"{v:.0%}", "n": f"{v:,.0f}", "mb": f"{v:,.0f} MB"}[
        kind
    ]


def render_kpis(k: dict) -> None:
    row1 = st.columns(4)
    row1[0].metric("Consultas", _fmt(k["consultas"], "n"))
    row1[1].metric(
        "Latencia p50", _fmt(k["p50"]), help="Mediana del tiempo total de respuesta"
    )
    row1[2].metric(
        "Latencia p95",
        _fmt(k["p95"]),
        help="95% de las consultas responde bajo este tiempo",
    )
    row1[3].metric("Tasa de error", _fmt(k["error_rate"], "%"))
    row2 = st.columns(4)
    row2[0].metric(
        "Citas verificadas",
        _fmt(k["grounded"], "%"),
        help="Proporción de páginas citadas que existen en los documentos recuperados",
    )
    row2[1].metric(
        "Consultas bloqueadas",
        _fmt(k["blocked_rate"], "%"),
        help="Guardrails + rate limit",
    )
    row2[2].metric(
        "Feedback positivo",
        _fmt(k["feedback_pos"], "%"),
        help=f"{k['feedback_n']} valoraciones",
    )
    row2[3].metric(
        "Tokens / consulta",
        _fmt(k["tokens_per_query"], "n"),
        help=f"Uso de modelo de respaldo: {_fmt(k['fallback_rate'], '%')} · RAM máx {_fmt(k['rss_mb'], 'mb')}",
    )
