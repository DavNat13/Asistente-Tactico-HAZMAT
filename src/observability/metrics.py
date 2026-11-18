"""Agregaciones de observabilidad para el dashboard (EV3 — IE1, IE2, IE3, IE4).

Precisión     : grounding de citas, feedback de usuarios, resultados de evals offline.
Latencia      : p50/p95 total, TTFT y desglose por nodo del grafo (cuellos de botella).
Consistencia  : evals con repeticiones (similitud entre respuestas).
Errores       : tasa y tipo (cuota, timeout, BD, modelo saturado), fallback de modelo.
Recursos      : tokens por consulta, CPU s y memoria RSS del proceso.
Seguridad     : bloqueos por categoría, PII redactada, eventos de auditoría.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pandas as pd

from src.observability.store import RUNS_COLLECTION, get_db

_RUN_FIELDS = {
    "_id": 0,
    "run_id": 1,
    "created_at": 1,
    "channel": 1,
    "complexity": 1,
    "status": 1,
    "error_type": 1,
    "latency_ms": 1,
    "ttft_ms": 1,
    "nodes": 1,
    "tools": 1,
    "tokens_in": 1,
    "tokens_out": 1,
    "llm_calls": 1,
    "key_rotations": 1,
    "model": 1,
    "model_fallback": 1,
    "blocked": 1,
    "block_reason": 1,
    "pii_redacted": 1,
    "grounded": 1,
    "citations": 1,
    "n_chunks": 1,
    "top_score": 1,
    "feedback": 1,
    "cpu_s": 1,
    "rss_mb": 1,
}


def load_runs(days: int, channel: str | None = None) -> pd.DataFrame:
    since = datetime.now(UTC) - timedelta(days=days)
    query: dict = {"created_at": {"$gte": since}}
    if channel:
        query["channel"] = channel
    rows = list(get_db()[RUNS_COLLECTION].find(query, _RUN_FIELDS).limit(20000))
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True)
    df["latency_s"] = df["latency_ms"] / 1000
    df["tokens"] = df["tokens_in"].fillna(0) + df["tokens_out"].fillna(0)
    return df


def _rate(df: pd.DataFrame, col: str) -> float:
    """Proporción de filas con la columna booleana en True (ausente o nulo = False)."""
    if col not in df:
        return 0.0
    return float(df[col].map(lambda v: v is True).mean())


def kpis(df: pd.DataFrame) -> dict:
    answered = df[df["status"] == "ok"]
    fb = df["feedback"].dropna() if "feedback" in df else pd.Series(dtype=float)
    llm = df[df["llm_calls"] > 0]
    return {
        "consultas": len(df),
        "p50": answered["latency_s"].quantile(0.5) if len(answered) else None,
        "p95": answered["latency_s"].quantile(0.95) if len(answered) else None,
        "ttft": answered["ttft_ms"].dropna().median() / 1000
        if answered["ttft_ms"].notna().any()
        else None,
        "error_rate": (df["status"] == "error").mean(),
        "blocked_rate": _rate(df, "blocked"),
        "grounded": df["grounded"].dropna().mean()
        if df["grounded"].notna().any()
        else None,
        "feedback_pos": (fb > 0).mean() if len(fb) else None,
        "feedback_n": len(fb),
        "tokens_per_query": llm["tokens"].mean() if len(llm) else 0,
        "fallback_rate": _rate(df, "model_fallback"),
        "rss_mb": df["rss_mb"].max(),
    }
