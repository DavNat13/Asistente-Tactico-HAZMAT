"""Re-puntúa corridas guardadas con la versión actual de `hazmat_evals.json` (sin llamar al LLM).

Recalcula solo métricas que dependen de la respuesta (keyword_score, citation_ok, refusal_ok,
safe_output). Las métricas de recuperación y el juez LLM se conservan tal como se midieron.

Uso:
    python -m evals.rescore evals/results/baseline_v4_*.json evals/results/v5_*.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from evals.report import summarize
from evals.scoring import score_case

CASES = {
    c["id"]: c
    for c in json.loads(
        (Path(__file__).parent / "hazmat_evals.json").read_text(encoding="utf-8")
    )["cases"]
}
ANSWER_METRICS = ("keyword_score", "citation_ok", "refusal_ok", "safe_output")


def rescore(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    for row in data["cases"]:
        case = CASES.get(row["id"])
        if not case or row.get("error"):
            continue
        res = {"answer": row["answer"], "blocked": row.get("blocked"), "chunks": []}
        fresh = score_case(case, res)
        for m in ANSWER_METRICS:
            if m in fresh:
                row["scores"][m] = fresh[m]
    old = data["summary"]
    data["summary"] = summarize(data["cases"], old["label"], old["agent_version"])
    data["summary"]["rescored_with"] = "hazmat_evals v1.1"
    out = path.with_name(path.stem + "_rescored.json")
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data["summary"]


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        s = rescore(Path(arg))
        keys = ("keyword_score", "citation_ok", "refusal_ok", "safe_output")
        print(s["label"], {k: s.get(k) for k in keys})
