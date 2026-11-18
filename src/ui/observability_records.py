"""Pestañas de evaluación offline y registro de ejecuciones del dashboard."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.ui.charts_eval import eval_compare
from src.ui.observability_tabs import EMPTY, EVAL_METRICS


def tab_evals(evals: pd.DataFrame) -> None:
    st.caption(
        "Corridas del set de evaluación (`python -m evals.run_evals`): 31 preguntas con respuesta "
        "conocida, ejecutadas de forma automática. No incluyen consultas de usuarios."
    )
    if evals.empty:
        st.info(
            "Aún no hay corridas de evaluación guardadas (usa --save-db).",
            icon=":material/science:",
        )
        return
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
        evals[[c for c in cols if c in evals]], hide_index=True, width="stretch"
    )


def tab_log(runs: pd.DataFrame) -> None:
    if runs.empty:
        st.info(EMPTY, icon=":material/hourglass_empty:")
        return
    st.caption("Últimas 200 ejecuciones. El usuario aparece seudonimizado (hash).")
    cols = [
        "created_at",
        "user",
        "complexity",
        "status",
        "latency_s",
        "tokens",
        "citations",
        "grounded",
        "model",
        "error_type",
        "block_reason",
        "feedback",
        "run_id",
    ]
    df = runs.sort_values("created_at", ascending=False).head(200)
    st.dataframe(
        df[[c for c in cols if c in df]],
        hide_index=True,
        width="stretch",
        column_config={
            "created_at": st.column_config.DatetimeColumn(
                "Fecha", format="DD/MM HH:mm:ss"
            ),
            "latency_s": st.column_config.NumberColumn("Latencia (s)", format="%.1f"),
            "grounded": st.column_config.ProgressColumn(
                "Citas verificadas", min_value=0, max_value=1
            ),
        },
    )
