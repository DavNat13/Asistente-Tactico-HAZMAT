"""Tareas programadas (GitHub Actions o cron).

    python -m src.automation.jobs health-check     # cada 30 min: latencia, errores, bloqueos
    python -m src.automation.jobs weekly-report    # lunes: resumen semanal al admin
    python -m src.automation.jobs nightly-eval     # diario: set de evaluación + regresiones

Los avisos se envían por correo a ADMIN_EMAILS; cada tipo de alerta se envía como máximo una vez
cada ALERT_COOLDOWN_H horas (colección `alerts`). Código de salida 1 si hay problemas (visible en CI).
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import UTC, datetime, timedelta

from src.automation.health import eval_regressions, health_alerts, weekly_rows
from src.config.features import features
from src.notify.notifications import notify_admins
from src.observability.store import RUNS_COLLECTION, get_db

ALERTS = "alerts"


def _runs(since: datetime, channel: str = "ui") -> list[dict]:
    query = {"created_at": {"$gte": since}, "channel": channel}
    return list(get_db()[RUNS_COLLECTION].find(query, {"_id": 0}))


def _cooldown_ok(kind: str) -> bool:
    since = datetime.now(UTC) - timedelta(hours=features.ALERT_COOLDOWN_H)
    return not get_db()[ALERTS].find_one({"kind": kind, "sent_at": {"$gte": since}})


def health_check() -> int:
    since = datetime.now(UTC) - timedelta(minutes=features.ALERT_WINDOW_MIN)
    alerts = [a for a in health_alerts(_runs(since)) if _cooldown_ok(a[0])]
    for kind, detail in alerts:
        notify_admins(
            f"⚠ Asistente HAZMAT: alerta de {kind}",
            "Alerta de salud del sistema",
            [
                ("Detalle", detail),
                ("Ventana", f"últimos {features.ALERT_WINDOW_MIN} min"),
            ],
            "Se detectó un comportamiento anormal en el asistente.",
            kind=f"alert_{kind}",
        )
        get_db()[ALERTS].insert_one(
            {"kind": kind, "detail": detail, "sent_at": datetime.now(UTC)}
        )
    print(f"health-check: {len(alerts)} alerta(s)", *[a[1] for a in alerts], sep="\n  ")
    return 1 if alerts else 0


def weekly_report() -> int:
    runs = _runs(datetime.now(UTC) - timedelta(days=7))
    rows = weekly_rows(runs)
    notify_admins(
        "Asistente HAZMAT · Reporte semanal",
        "Reporte semanal de uso y calidad",
        rows,
        "Resumen de los últimos 7 días (solo uso real de la aplicación).",
        kind="weekly_report",
    )
    print("weekly-report:", *[f"{k}: {v}" for k, v in rows], sep="\n  ")
    return 0


def nightly_eval() -> int:
    label = f"nightly-{datetime.now(UTC):%Y%m%d}"
    cmd = [
        sys.executable,
        "-m",
        "evals.run_evals",
        "--label",
        label,
        "--save-db",
        "--include-db-cases",
    ]
    code = subprocess.run(cmd, check=False).returncode
    runs = list(get_db()["eval_runs"].find({}, {"summary": 1}).sort("_id", -1).limit(2))
    if code != 0 or not runs:
        notify_admins(
            "✖ Evaluación nocturna falló",
            "Evaluación nocturna",
            [("Código", str(code))],
            "La evaluación automática no terminó correctamente.",
            kind="nightly_eval",
        )
        return 1
    current, previous = (
        runs[0]["summary"],
        (runs[1]["summary"] if len(runs) > 1 else None),
    )
    issues = eval_regressions(current, previous)
    rows = [
        (k, f"{current[k]:.0%}")
        for k in ("keyword_score", "citation_ok", "refusal_ok")
        if current.get(k) is not None
    ]
    rows += [("Latencia p95", f"{current.get('latency_p95_s', 0):.1f} s")] + [
        ("Problema", i) for i in issues
    ]
    if issues:
        notify_admins(
            "⚠ Regresión en la evaluación nocturna",
            "Evaluación nocturna",
            rows,
            "La calidad del asistente bajó respecto de la corrida anterior.",
            kind="nightly_eval",
        )
    print("nightly-eval:", *[f"{k}: {v}" for k, v in rows], sep="\n  ")
    return 1 if issues else 0


TASKS = {
    "health-check": health_check,
    "weekly-report": weekly_report,
    "nightly-eval": nightly_eval,
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Tareas automatizadas del Asistente HAZMAT"
    )
    parser.add_argument("task", choices=list(TASKS))
    sys.exit(TASKS[parser.parse_args().task]())
