"""Indicadores del panel con semáforo y explicación (qué significa, referencia y qué hacer)."""

from __future__ import annotations

import pandas as pd

from src.config.features import features
from src.observability.health_status import kpi_states
from src.ui.ui_kit import stat_tile, tiles


def _fmt(v, kind: str = "s") -> str:
    if v is None or pd.isna(v):
        return "—"
    return {"s": f"{v:.1f} s", "%": f"{v:.0%}", "n": f"{v:,.0f}", "mb": f"{v:,.0f} MB"}[
        kind
    ]


def render_kpis(k: dict) -> None:
    s = kpi_states(k)
    thr = features.ALERT_P95_S
    tiles(
        [
            stat_tile(
                "Consultas",
                _fmt(k["consultas"], "n"),
                "info",
                "en el periodo elegido",
                "message",
                "Cantidad de preguntas respondidas o bloqueadas en el periodo.",
            ),
            stat_tile(
                "Latencia típica (p50)",
                _fmt(k["p50"]),
                s["p50"],
                "la mitad responde en menos",
                "clock",
                "Mediana del tiempo total de respuesta. Si sube, el modelo está lento o saturado.",
            ),
            stat_tile(
                "Latencia p95",
                _fmt(k["p95"]),
                s["p95"],
                f"umbral de alerta {thr:g} s",
                "gauge",
                "El 95% de las respuestas llega antes de este tiempo. Sobre el umbral se avisa al admin.",
            ),
            stat_tile(
                "Tasa de error",
                _fmt(k["error_rate"], "%"),
                s["error_rate"],
                f"alerta sobre {features.ALERT_ERROR_RATE:.0%}",
                "alert",
                "Consultas que fallaron (timeout, cuota, BD). En rojo: revisar API keys y el log.",
            ),
            stat_tile(
                "Citas verificadas",
                _fmt(k["grounded"], "%"),
                s["grounded"],
                "páginas citadas que existen",
                "file",
                "Proporción de páginas citadas que están en los documentos recuperados (anti-alucinación).",
            ),
            stat_tile(
                "Consultas bloqueadas",
                _fmt(k["blocked_rate"], "%"),
                s["blocked_rate"],
                "guardrails y límite de uso",
                "ban",
                "Intentos de manipulación, fuera de dominio o abuso detenidos antes del modelo.",
            ),
            stat_tile(
                "Feedback positivo",
                _fmt(k["feedback_pos"], "%"),
                s["feedback_pos"],
                f"{k['feedback_n']} valoraciones 👍/👎",
                "thumbs",
                "Opinión de los usuarios. Cada 👎 se convierte en un caso candidato de evaluación.",
            ),
            stat_tile(
                "Tokens por consulta",
                _fmt(k["tokens_per_query"], "n"),
                "info",
                f"respaldo {_fmt(k['fallback_rate'], '%')} · RAM {_fmt(k['rss_mb'], 'mb')}",
                "coins",
                "Consumo promedio del modelo (costo). Incluye uso de modelo de respaldo y memoria máxima.",
            ),
        ]
    )
