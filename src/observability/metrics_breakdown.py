"""Desgloses del dashboard: latencia temporal, por nodo, por nivel, errores, seguridad y evals."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pandas as pd

from src.observability.store import SECURITY_COLLECTION, get_db


def latency_over_time(df: pd.DataFrame, freq: str) -> pd.DataFrame:
    ok = df[df["status"] == "ok"].set_index("created_at")
    if ok.empty:
        return pd.DataFrame(columns=["created_at", "p50", "p95", "n"])
    g = ok["latency_s"].resample(freq)
    out = pd.DataFrame({"p50": g.median(), "p95": g.quantile(0.95), "n": g.count()})
    return out[out["n"] > 0].reset_index()


def node_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    rows = [n for nodes in df["nodes"].dropna() for n in nodes]
    if not rows:
        return pd.DataFrame(columns=["node", "ms", "calls"])
    nodes = pd.DataFrame(rows)
    out = nodes.groupby("node")["ms"].agg(["mean", "count"]).reset_index()
    out.columns = ["node", "ms", "calls"]
    return out.sort_values("ms", ascending=False)


def by_level(df: pd.DataFrame) -> pd.DataFrame:
    d = df.dropna(subset=["complexity"])
    if d.empty:
        return pd.DataFrame(columns=["complexity", "consultas", "p50", "tokens"])
    out = d.groupby("complexity").agg(
        consultas=("run_id", "count"),
        p50=("latency_s", "median"),
        tokens=("tokens", "mean"),
    )
    order = ["low", "medium", "high"]
    return out.reindex([o for o in order if o in out.index]).reset_index()


def errors(df: pd.DataFrame) -> pd.DataFrame:
    e = df[df["status"] == "error"]
    return (
        e.groupby("error_type")
        .size()
        .rename("n")
        .reset_index()
        .sort_values("n", ascending=False)
    )


def security_events(days: int) -> pd.DataFrame:
    since = datetime.now(UTC) - timedelta(days=days)
    rows = list(
        get_db()[SECURITY_COLLECTION].find(
            {"created_at": {"$gte": since}}, {"_id": 0, "user": 0}
        )
    )
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(columns=["kind", "n"])
    return (
        df.groupby("kind")
        .size()
        .rename("n")
        .reset_index()
        .sort_values("n", ascending=False)
    )


def eval_runs(limit: int = 10) -> pd.DataFrame:
    rows = list(
        get_db()["eval_runs"]
        .find({}, {"_id": 0, "summary": 1})
        .sort("_id", -1)
        .limit(limit)
    )
    return pd.DataFrame([r["summary"] for r in rows if "summary" in r])
