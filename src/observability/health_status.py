"""Semáforo del panel de observabilidad (lógica pura, testeable sin UI ni base de datos).

Usa los mismos umbrales que las alertas por correo (`ALERT_P95_S`, `ALERT_ERROR_RATE`,
`ALERT_BLOCKED_RATE`): lo que se ve en rojo aquí es lo que dispara un aviso al administrador.
"""

from __future__ import annotations

import pandas as pd

from src.automation.health import health_alerts
from src.config.features import features

# Tipo de alerta → gravedad. La seguridad es "atención": bloquear ataques es el sistema funcionando.
SEVERITY = {"latency": "warn", "errors": "crit", "security": "warn"}


def _bad(v) -> bool:
    return v is None or (isinstance(v, float) and pd.isna(v))


def overall(runs: pd.DataFrame) -> tuple[str, str, list[str]]:
    """(estado, título, detalles) para la banda superior."""
    if runs.empty:
        return (
            "neutral",
            "Sin consultas en el periodo",
            ["Usa el chat y vuelve: los datos aparecen en segundos."],
        )
    cols = [c for c in ("status", "latency_ms", "blocked") if c in runs]
    alerts = health_alerts(runs[cols].to_dict("records"))
    if not alerts:
        return (
            "ok",
            "Todo en orden",
            [
                f"Latencia, errores y bloqueos dentro de los umbrales en {len(runs)} consultas."
            ],
        )
    state = "crit" if any(SEVERITY.get(k) == "crit" for k, _ in alerts) else "warn"
    title = "Requiere acción" if state == "crit" else "Revisar"
    return state, title, [detail for _, detail in alerts]


def _grade(value, warn_if, crit_if=None) -> str:
    """neutral sin dato; crit/warn si se cumple la condición; ok en otro caso."""
    if _bad(value):
        return "neutral"
    if crit_if and crit_if(value):
        return "crit"
    return "warn" if warn_if(value) else "ok"


def kpi_states(k: dict) -> dict[str, str]:
    """Estado por indicador (ok / warn / crit / neutral)."""
    thr = features.ALERT_P95_S
    return {
        "p95": _grade(k.get("p95"), lambda v: v > thr, lambda v: v > thr * 1.5),
        "p50": _grade(k.get("p50"), lambda v: v > thr * 0.6),
        "error_rate": _grade(
            k.get("error_rate"),
            lambda v: v > 0,
            lambda v: v > features.ALERT_ERROR_RATE,
        ),
        "blocked_rate": _grade(
            k.get("blocked_rate"), lambda v: v > features.ALERT_BLOCKED_RATE
        ),
        "grounded": _grade(k.get("grounded"), lambda v: v < 0.95, lambda v: v < 0.8),
        "feedback_pos": _grade(
            k.get("feedback_pos"), lambda v: v < 0.8, lambda v: v < 0.6
        ),
    }
