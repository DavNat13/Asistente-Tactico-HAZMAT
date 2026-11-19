"""Pestañas "Evaluación offline" y "Registro" del panel de observabilidad."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.ui.charts_eval import eval_compare
from src.ui.ui_kit import card, empty_state, stat_tile, tiles

EVAL_METRICS = [
    "keyword_score",
    "retrieval_hit",
    "citation_ok",
    "refusal_ok",
    "safe_output",
    "consistency",
]
EVAL_NAMES = {
    "keyword_score": (
        "Datos correctos",
        "file",
        "Respuestas que contienen los datos clave esperados.",
    ),
    "retrieval_hit": (
        "Página correcta encontrada",
        "book",
        "La búsqueda trajo la página correcta de la GRE.",
    ),
    "citation_ok": (
        "Citas válidas",
        "check",
        "Las páginas citadas existen en lo recuperado.",
    ),
    "refusal_ok": (
        "Rechazos correctos",
        "ban",
        "Ataques y preguntas fuera de dominio rechazados.",
    ),
    "safe_output": (
        "Salida segura",
        "shield",
        "Sin HTML, secretos ni datos personales en la respuesta.",
    ),
    "consistency": (
        "Consistencia",
        "layers",
        "Respuestas parecidas al repetir la misma pregunta.",
    ),
}
EMPTY = "Aún no hay consultas en este periodo. Usa el chat y vuelve aquí: los datos aparecen en segundos."


def _state(v: float) -> str:
    return "ok" if v >= 0.9 else "warn" if v >= 0.75 else "crit"


def tab_evals(evals: pd.DataFrame) -> None:
    if evals.empty:
        empty_state(
            "Aún no hay corridas guardadas. Ejecuta `python -m evals.run_evals --save-db`.",
            "activity",
        )
        return
    last = evals.iloc[0]
    tiles(
        [
            stat_tile(
                name, f"{last[k]:.0%}", _state(last[k]), "última corrida", ic, hint
            )
            for k, (name, ic, hint) in EVAL_NAMES.items()
            if k in evals and pd.notna(last[k])
        ]
    )
    with card(
        "eval_compare",
        "Comparación entre corridas",
        "Las 3 corridas más recientes del set de 31 preguntas con respuesta conocida",
        "Cada noche se ejecutan las mismas preguntas. Si una barra baja respecto de la corrida "
        "anterior hay una **regresión**: algo empeoró y se avisa por correo al admin.",
    ):
        st.altair_chart(eval_compare(evals, EVAL_METRICS), width="stretch")
    with card("eval_table", "Detalle de corridas"):
        cols = ["label", "timestamp", "n_cases", "latency_p50_s", "latency_p95_s"]
        st.dataframe(
            evals[[c for c in [*cols, *EVAL_METRICS] if c in evals]],
            hide_index=True,
            width="stretch",
        )


def tab_log(runs: pd.DataFrame) -> None:
    if runs.empty:
        empty_state(EMPTY, "activity")
        return
    with card(
        "log",
        "Últimas 200 ejecuciones",
        "Una fila por consulta. El usuario aparece seudonimizado (hash).",
        "Úsalo para investigar un caso puntual: filtra por **status = error** o por "
        "**block_reason** y copia el `run_id` para buscar la traza en LangSmith.",
    ):
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
                "latency_s": st.column_config.NumberColumn(
                    "Latencia (s)", format="%.1f"
                ),
                "grounded": st.column_config.ProgressColumn(
                    "Citas verificadas", min_value=0, max_value=1
                ),
            },
        )
