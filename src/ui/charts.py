"""Gráficos del dashboard (Altair). Paleta de referencia validada (CVD-safe) en orden fijo.

Reglas: un solo eje Y por gráfico, marcas finas (barras con extremo redondeado de 4px, líneas de 2px),
tooltip en cada marca, leyenda solo con >= 2 series, grilla recesiva, texto nunca en color de serie.
"""

from __future__ import annotations

import altair as alt
import pandas as pd

SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]  # slots 1-3 de la paleta categórica
CRITICAL = "#d03b3b"  # estado "crítico" (reservado para errores)
LEVEL_NAMES = {"low": "Bajo", "medium": "Medio", "high": "Alto"}
NODE_NAMES = {
    "guard_in": "Guardrail entrada",
    "classify": "Clasificación",
    "prefetch": "Recuperación (RAG)",
    "agent": "LLM (agente)",
    "tools": "Herramientas",
    "guard_out": "Verificación salida",
    "direct": "Respuesta directa",
}


def _base(chart: alt.Chart, height: int = 220) -> alt.Chart:
    return (
        chart.properties(height=height)
        .configure_axis(
            grid=True,
            gridOpacity=0.35,
            domain=False,
            tickColor="transparent",
            labelFontSize=11,
            titleFontSize=11,
            titleFontWeight="normal",
        )
        .configure_view(strokeWidth=0)
    )


def latency_line(df: pd.DataFrame) -> alt.Chart:
    """p50 y p95 en el tiempo: dos series → leyenda + etiqueta directa vía tooltip."""
    long = df.melt(
        id_vars=["created_at", "n"],
        value_vars=["p50", "p95"],
        var_name="métrica",
        value_name="seg",
    )
    color = alt.Color(
        "métrica:N",
        scale=alt.Scale(domain=["p50", "p95"], range=SERIES[:2]),
        legend=alt.Legend(orient="top", title=None),
    )
    hover = alt.selection_point(
        fields=["created_at"], nearest=True, on="pointerover", empty=False
    )
    x = alt.X("created_at:T", title=None)
    lines = (
        alt.Chart(long)
        .mark_line(strokeWidth=2, interpolate="monotone")
        .encode(x=x, y=alt.Y("seg:Q", title="segundos"), color=color)
    )
    points = (
        lines.mark_point(size=70, filled=True, stroke="white", strokeWidth=2)
        .encode(
            opacity=alt.condition(hover, alt.value(1), alt.value(0)),
            tooltip=[
                alt.Tooltip("created_at:T", title="Periodo"),
                "métrica:N",
                alt.Tooltip("seg:Q", format=".1f", title="Seg"),
                alt.Tooltip("n:Q", title="Consultas"),
            ],
        )
        .add_params(hover)
    )
    rule = (
        alt.Chart(long)
        .mark_rule(strokeWidth=1, opacity=0.4)
        .encode(x=x)
        .transform_filter(hover)
    )
    return _base(alt.layer(lines, points, rule))


def hbar(
    df: pd.DataFrame,
    cat: str,
    val: str,
    title: str,
    names: dict | None = None,
    color: str = SERIES[0],
    fmt: str = ".0f",
) -> alt.Chart:
    d = df.copy()
    if names:
        d[cat] = d[cat].map(lambda v: names.get(v, v))
    chart = (
        alt.Chart(d)
        .mark_bar(cornerRadiusEnd=4, height=14, color=color)
        .encode(
            y=alt.Y(f"{cat}:N", sort="-x", title=None),
            x=alt.X(f"{val}:Q", title=title),
            tooltip=[
                alt.Tooltip(f"{cat}:N", title=""),
                alt.Tooltip(f"{val}:Q", format=fmt, title=title),
            ],
        )
    )
    labels = chart.mark_text(align="left", dx=4, fontSize=11, color="gray").encode(
        text=alt.Text(f"{val}:Q", format=fmt)
    )
    return _base(chart + labels, height=max(90, 30 * len(d)))


def level_bars(df: pd.DataFrame) -> alt.Chart:
    d = df.assign(nivel=df["complexity"].map(LEVEL_NAMES))
    return hbar(d, "nivel", "p50", "latencia p50 (s)", fmt=".1f")
