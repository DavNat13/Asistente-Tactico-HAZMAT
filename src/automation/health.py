"""Reglas de salud y regresión (lógica pura, testeable sin base de datos)."""

from __future__ import annotations

import math

from src.config.features import features


def _p95(values: list[float]) -> float:
    if not values:
        return 0.0
    v = sorted(values)
    return v[min(len(v) - 1, math.ceil(0.95 * len(v)) - 1)]


def health_alerts(runs: list[dict]) -> list[tuple[str, str]]:
    """Evalúa una ventana de ejecuciones (canal ui). Devuelve [(tipo, detalle)]."""
    if not runs:
        return []
    n = len(runs)
    ok = [
        r["latency_ms"] / 1000
        for r in runs
        if r.get("status") == "ok" and r.get("latency_ms")
    ]
    errors = sum(1 for r in runs if r.get("status") == "error")
    blocked = sum(1 for r in runs if r.get("blocked"))
    alerts = []
    p95 = _p95(ok)
    if len(ok) >= 3 and p95 > features.ALERT_P95_S:
        alerts.append(
            (
                "latency",
                f"Latencia p95 de {p95:.1f} s (umbral {features.ALERT_P95_S:g} s) en {len(ok)} respuestas",
            )
        )
    if n >= 3 and errors / n > features.ALERT_ERROR_RATE:
        alerts.append(
            ("errors", f"Tasa de error {errors / n:.0%} ({errors} de {n} consultas)")
        )
    if n >= 5 and blocked / n > features.ALERT_BLOCKED_RATE:
        alerts.append(
            (
                "security",
                f"{blocked} de {n} consultas bloqueadas por seguridad ({blocked / n:.0%})",
            )
        )
    return alerts


def eval_regressions(current: dict, previous: dict | None) -> list[str]:
    """Compara dos resúmenes de evaluación. Devuelve los problemas detectados."""
    issues = []
    kw, cit, err = (
        current.get("keyword_score"),
        current.get("citation_ok"),
        current.get("error_rate") or 0,
    )
    if previous and kw is not None and previous.get("keyword_score") is not None:
        drop = previous["keyword_score"] - kw
        if drop > 0.10:
            issues.append(
                f"Precisión bajó {drop:.0%} (de {previous['keyword_score']:.0%} a {kw:.0%})"
            )
    if cit is not None and cit < 0.90:
        issues.append(f"Citas correctas en {cit:.0%} (mínimo 90%)")
    if err > 0.10:
        issues.append(f"Tasa de error {err:.0%} (máximo 10%)")
    return issues


def weekly_rows(runs: list[dict]) -> list[tuple[str, str]]:
    n = len(runs)
    if not n:
        return [("Consultas", "0")]
    ok = [
        r["latency_ms"] / 1000
        for r in runs
        if r.get("status") == "ok" and r.get("latency_ms")
    ]
    fb = [r["feedback"] for r in runs if r.get("feedback") in (1, -1)]
    grounded = [
        r["grounded"] for r in runs if isinstance(r.get("grounded"), (int, float))
    ]
    users = {r.get("user") for r in runs if r.get("user")}
    counts: dict[str, int] = {}
    for r in runs:
        for un in r.get("un_numbers") or []:
            counts[un] = counts.get(un, 0) + 1
    top = ", ".join(
        f"UN {u} ({c})" for u, c in sorted(counts.items(), key=lambda x: -x[1])[:5]
    )
    return [
        ("Consultas", str(n)),
        ("Usuarios activos", str(len(users))),
        ("Latencia mediana", f"{sorted(ok)[len(ok) // 2]:.1f} s" if ok else "—"),
        ("Latencia p95", f"{_p95(ok):.1f} s" if ok else "—"),
        (
            "Tasa de error",
            f"{sum(1 for r in runs if r.get('status') == 'error') / n:.0%}",
        ),
        (
            "Citas verificadas",
            f"{sum(grounded) / len(grounded):.0%}" if grounded else "—",
        ),
        ("Consultas bloqueadas", str(sum(1 for r in runs if r.get("blocked")))),
        (
            "Feedback positivo",
            f"{sum(1 for f in fb if f > 0) / len(fb):.0%} de {len(fb)}"
            if fb
            else "Sin valoraciones",
        ),
        ("Materiales más consultados", top or "—"),
    ]
