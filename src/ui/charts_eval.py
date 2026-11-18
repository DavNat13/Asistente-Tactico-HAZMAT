"""Gráfico de comparación de corridas de evaluación offline."""

from __future__ import annotations

import altair as alt
import pandas as pd

from src.ui.charts import SERIES, _base


def eval_compare(evals: pd.DataFrame, metrics: list[str]) -> alt.Chart:
    """Métricas de evaluación por corrida (≥2 corridas → leyenda arriba)."""
    d = evals.melt(
        id_vars=["label"],
        value_vars=[m for m in metrics if m in evals],
        var_name="métrica",
        value_name="valor",
    ).dropna()
    labels = list(dict.fromkeys(d["label"]))[:3]
    d = d[d["label"].isin(labels)]
    return _base(
        alt.Chart(d)
        .mark_bar(cornerRadiusEnd=4, height=10)
        .encode(
            y=alt.Y("label:N", title=None, axis=None),
            x=alt.X(
                "valor:Q",
                title=None,
                scale=alt.Scale(domain=[0, 1]),
                axis=alt.Axis(format="%"),
            ),
            color=alt.Color(
                "label:N",
                scale=alt.Scale(domain=labels, range=SERIES[: len(labels)]),
                legend=alt.Legend(orient="top", title=None),
            ),
            row=alt.Row(
                "métrica:N",
                title=None,
                header=alt.Header(labelAngle=0, labelAlign="left"),
            ),
            tooltip=["label:N", "métrica:N", alt.Tooltip("valor:Q", format=".0%")],
        ),
        height=30,
    )
