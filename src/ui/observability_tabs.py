"""Pestañas "Uso real" y "Seguridad": cuadrícula de tarjetas, un gráfico por tarjeta, cada una con su
explicación ("¿Qué significa?")."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.observability import metrics as m
from src.observability import metrics_breakdown as mb
from src.ui import charts
from src.ui.kpis import render_kpis
from src.ui.observability_help import EVENT_NAMES
from src.ui.ui_kit import card, empty_state, stat_tile, tiles

EMPTY = "Aún no hay consultas en este periodo. Usa el chat y vuelve aquí: los datos aparecen en segundos."


def _chart(chart) -> None:
    st.altair_chart(chart, width="stretch")


def tab_usage(runs: pd.DataFrame, freq: str) -> None:
    if runs.empty:
        empty_state(EMPTY, "activity")
        return
    render_kpis(m.kpis(runs))
    with card(
        "latency",
        "Latencia en el tiempo",
        "Mediana (p50) y percentil 95 de las respuestas exitosas",
        "Si la línea **p95** sube, algunas respuestas tardan demasiado (modelo saturado o "
        "timeouts). Si sube también la **p50**, la lentitud es general. Pasa el cursor para ver "
        "cuántas consultas hubo en cada periodo.",
    ):
        _chart(charts.latency_line(mb.latency_over_time(runs, freq)))
    left, right = st.columns(2, gap="medium")
    with (
        left,
        card(
            "nodes",
            "Dónde se va el tiempo",
            "Tiempo medio por etapa del agente (ms)",
            "Cada consulta pasa por etapas: guardrail, recuperación de la GRE (RAG), modelo (LLM) y "
            "verificación. La barra más larga es el **cuello de botella** a optimizar.",
        ),
    ):
        _chart(
            charts.hbar(mb.node_breakdown(runs), "node", "ms", "ms", charts.NODE_NAMES)
        )
    with (
        right,
        card(
            "levels",
            "Latencia por nivel",
            "Bajo = sin modelo · Medio = RAG · Alto = plan de respuesta",
            "El asistente clasifica cada consulta. Es normal que **Alto** tarde más: arma un plan "
            "completo con varias herramientas. Un nivel **Bajo** lento indica un problema.",
        ),
    ):
        _chart(charts.level_bars(mb.by_level(runs)))
    with card(
        "errors",
        "Errores por tipo",
        "Consultas que no obtuvieron respuesta",
        "**timeout**: el modelo no respondió a tiempo · **quota**: se agotó la cuota de la API · "
        "**database**: MongoDB no respondió · **llm_unavailable**: modelo saturado (se usa respaldo).",
    ):
        err = mb.errors(runs)
        if err.empty:
            empty_state("Sin errores en el periodo.", "check")
        else:
            _chart(
                charts.hbar(err, "error_type", "n", "consultas", color=charts.CRITICAL)
            )


def tab_security(runs: pd.DataFrame, sec: pd.DataFrame) -> None:
    blocked = (
        int(runs["blocked"].map(lambda v: v is True).sum()) if "blocked" in runs else 0
    )
    pii = int(runs["pii_redacted"].fillna(0).sum()) if "pii_redacted" in runs else 0
    audit = int(sec["n"].sum()) if not sec.empty else 0
    tiles(
        [
            stat_tile(
                "Consultas bloqueadas",
                f"{blocked}",
                "warn" if blocked else "ok",
                "antes de llegar al modelo",
                "ban",
                "Manipulación, intención de daño, fuera de dominio o límite de uso.",
            ),
            stat_tile(
                "Datos personales ocultados",
                f"{pii}",
                "info",
                "RUT, teléfonos, correos y patentes",
                "eyeoff",
                "Datos reemplazados automáticamente antes de enviar el texto al modelo de IA.",
            ),
            stat_tile(
                "Eventos de auditoría",
                f"{audit}",
                "info",
                "cuentas y accesos",
                "file",
                "Registros de seguridad: inicios de sesión, registros, códigos y cambios de contraseña.",
            ),
        ]
    )
    left, right = st.columns(2, gap="medium")
    with (
        left,
        card(
            "blocks",
            "Bloqueos por categoría",
            "Qué se intentó y fue detenido",
            "Los **guardrails** revisan cada consulta antes del modelo. Muchos bloqueos de "
            "*manipulación* seguidos pueden indicar un ataque: revisa la pestaña Registro.",
        ),
    ):
        reasons = mb.blocked_by_reason(runs)
        if reasons.empty:
            empty_state("Sin bloqueos en el periodo.", "check")
        else:
            _chart(
                charts.hbar(reasons, "reason", "n", "consultas", color=charts.SERIES[1])
            )
    with (
        right,
        card(
            "audit",
            "Eventos de auditoría",
            "Actividad de cuentas registrada en security_events",
            "Muchos **inicios de sesión fallidos** pueden ser un intento de fuerza bruta (la cuenta "
            "se bloquea tras 5). Los usuarios están seudonimizados.",
        ),
    ):
        if sec.empty:
            empty_state("Sin eventos en el periodo.", "check")
        else:
            _chart(charts.hbar(sec, "kind", "n", "eventos", EVENT_NAMES))
