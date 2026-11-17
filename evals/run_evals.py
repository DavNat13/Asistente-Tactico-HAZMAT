"""Evaluación offline del Asistente HAZMAT (EV3 — IE1/IE2).

Métricas: retrieval_hit, page_hit, citation_ok, keyword_score, refusal_ok, safe_output,
tool_policy_ok, consistency (--repeat), faithfulness (--judge), latencia p50/p95, tokens, error_rate.

Uso:
    python -m evals.run_evals --label baseline
    python -m evals.run_evals --label v5 --repeat 3 --judge --save-db
    python -m evals.run_evals --only M01,H01
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evals.report import summarize
from evals.runner import load_runner
from evals.scoring import judge_faithfulness, score_case, similarity

EVALS_PATH = Path(__file__).parent / "hazmat_evals.json"
RESULTS_DIR = Path(__file__).parent / "results"


def run_case(run, case: dict, args, consistency_ids: list[str]) -> dict:
    t0 = time.perf_counter()
    try:
        res, err = run(case["question"]), None
    except Exception as e:  # noqa: BLE001
        res, err = {"answer": "", "chunks": []}, f"{type(e).__name__}: {str(e)[:200]}"
    latency = time.perf_counter() - t0
    scores = score_case(case, res) if not err else {}
    if args.judge and not err and case["level"] in ("medium", "high"):
        f = judge_faithfulness(
            case["question"], res.get("answer", ""), res.get("chunks", [])
        )
        if f is not None:
            scores["faithfulness"] = f
    if args.repeat > 1 and case["id"] in consistency_ids and not err:
        answers = [res.get("answer", "")]
        for _ in range(args.repeat - 1):
            time.sleep(args.sleep)
            try:
                answers.append(run(case["question"]).get("answer", ""))
            except Exception:  # noqa: BLE001
                answers.append("")
        scores["consistency"] = round(similarity(answers), 3)
    return {
        "id": case["id"],
        "level": case["level"],
        "question": case["question"],
        "answer": res.get("answer", ""),
        "complexity_pred": res.get("complexity"),
        "blocked": res.get("blocked", False),
        "latency_s": round(latency, 3),
        "tool_calls": res.get("tool_calls", 0),
        "tokens_in": res.get("tokens_in", 0),
        "tokens_out": res.get("tokens_out", 0),
        "n_chunks": len(res.get("chunks") or []),
        "error": err,
        "scores": scores,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", default="run")
    ap.add_argument("--only", default="", help="IDs separados por coma")
    ap.add_argument(
        "--repeat", type=int, default=1, help="repeticiones para consistencia"
    )
    ap.add_argument("--judge", action="store_true", help="juez LLM de fidelidad")
    ap.add_argument(
        "--save-db", action="store_true", help="guardar en MongoDB (eval_runs)"
    )
    ap.add_argument(
        "--sleep", type=float, default=1.0, help="pausa entre casos (cuota API)"
    )
    args = ap.parse_args()

    data = json.loads(EVALS_PATH.read_text(encoding="utf-8"))
    cases = data["cases"]
    if args.only:
        cases = [c for c in cases if c["id"] in set(args.only.split(","))]

    run, version = load_runner()
    rows = []
    for case in cases:
        row = run_case(run, case, args, data.get("consistency_ids", []))
        rows.append(row)
        flag = (
            "ERR " + row["error"]
            if row["error"]
            else " ".join(f"{k}={v}" for k, v in row["scores"].items())
        )
        print(
            f"[{case['id']}] {row['latency_s']:5.1f}s tools={row['tool_calls']} {flag}",
            flush=True,
        )
        time.sleep(args.sleep)

    summary = summarize(rows, args.label, version)
    RESULTS_DIR.mkdir(exist_ok=True)
    out = (
        RESULTS_DIR
        / f"{args.label}_{datetime.now(tz=UTC).strftime('%Y%m%d_%H%M%S')}.json"
    )
    out.write_text(
        json.dumps({"summary": summary, "cases": rows}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(
        "\n"
        + json.dumps(summary, ensure_ascii=False, indent=2)
        + f"\n\nResultados: {out}"
    )

    if args.save_db:
        from pymongo import MongoClient

        from src.config.settings import settings

        client = MongoClient(settings.MONGODB_URI, serverSelectionTimeoutMS=8000)
        client[settings.MONGODB_DB_NAME]["eval_runs"].insert_one(
            {"summary": summary, "cases": rows}
        )
        print("Guardado en MongoDB: eval_runs")


if __name__ == "__main__":
    main()
