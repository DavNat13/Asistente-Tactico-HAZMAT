"""Agregación de métricas de una corrida de evaluación."""

from __future__ import annotations

import itertools
from datetime import UTC, datetime

from evals.scoring import mean_of, pctl

METRICS = (
    "retrieval_hit",
    "page_hit",
    "citation_ok",
    "keyword_score",
    "refusal_ok",
    "safe_output",
    "tool_policy_ok",
    "consistency",
    "faithfulness",
)


def summarize(rows: list[dict], label: str, version: str) -> dict:
    lat = [r["latency_s"] for r in rows if not r["error"]]
    by_level = {}
    for lvl, grp in itertools.groupby(
        sorted(rows, key=lambda r: r["level"]), key=lambda r: r["level"]
    ):
        rs = list(grp)
        by_level[lvl] = {
            "n": len(rs),
            "latency_p50_s": round(pctl([r["latency_s"] for r in rs], 0.5), 2),
            "keyword_score": mean_of(rs, "keyword_score"),
        }
    summary = {
        "label": label,
        "agent_version": version,
        "timestamp": datetime.now(tz=UTC).isoformat(),
        "n_cases": len(rows),
        "error_rate": round(sum(1 for r in rows if r["error"]) / max(len(rows), 1), 3),
        "latency_p50_s": round(pctl(lat, 0.5), 2),
        "latency_p95_s": round(pctl(lat, 0.95), 2),
        "tokens_in_total": sum(r["tokens_in"] for r in rows),
        "tokens_out_total": sum(r["tokens_out"] for r in rows),
    }
    summary.update({m: mean_of(rows, m) for m in METRICS})
    summary["by_level"] = by_level
    return summary
