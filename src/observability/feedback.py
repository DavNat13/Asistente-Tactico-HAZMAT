"""Ciclo de mejora continua: respuestas con 👎 → casos candidatos → casos de evaluación aprobados.

- `eval_candidates`: pregunta y respuesta (ya sin datos personales ni código), run_id, nivel, estado.
- `eval_cases`: casos aprobados por un admin con las palabras clave / páginas esperadas.
  `python -m evals.run_evals --include-db-cases` los suma al set fijo.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

from src.observability.store import get_db, run_async
from src.security.pii import redact
from src.security.text import strip_markup

log = logging.getLogger("hazmat.feedback")
CANDIDATES = "eval_candidates"
CASES = "eval_cases"


def save_candidate(
    run_id: str, question: str, answer: str, complexity: str | None
) -> None:
    question = redact(strip_markup(question))[0][:500]
    if not question:
        return
    doc = {
        "_id": run_id,
        "created_at": datetime.now(UTC),
        "question": question,
        "answer": redact(strip_markup(answer))[0][:3000],
        "complexity": complexity or "medium",
        "status": "pendiente",
    }

    def _write(d):
        try:
            get_db()[CANDIDATES].replace_one({"_id": d["_id"]}, d, upsert=True)
        except Exception as e:  # noqa: BLE001
            log.warning("No se pudo guardar el candidato: %s", type(e).__name__)

    run_async(_write, doc)


def list_candidates(status: str = "pendiente", limit: int = 50) -> list[dict]:
    cursor = (
        get_db()[CANDIDATES]
        .find({"status": status})
        .sort("created_at", -1)
        .limit(limit)
    )
    return list(cursor)


def _split(text: str) -> list[str]:
    return [t.strip() for t in (text or "").split(",") if t.strip()]


def approve(candidate_id: str, keywords: str, pages: str, admin: str) -> dict:
    cand = get_db()[CANDIDATES].find_one({"_id": candidate_id})
    if not cand:
        raise ValueError("Candidato no encontrado")
    kw = _split(keywords)
    if not kw:
        raise ValueError("Indica al menos un dato clave esperado (ej. 128, 50 m)")
    case = {
        "_id": f"DB-{uuid.uuid4().hex[:8]}",
        "level": cand.get("complexity") or "medium",
        "question": cand["question"],
        "keywords_all": kw,
        "pages": _split(pages),
        "source": "feedback",
        "approved_by": admin,
        "created_at": datetime.now(UTC),
    }
    get_db()[CASES].insert_one(case)
    get_db()[CANDIDATES].update_one(
        {"_id": candidate_id}, {"$set": {"status": "aprobado", "case_id": case["_id"]}}
    )
    return case


def reject(candidate_id: str) -> None:
    get_db()[CANDIDATES].update_one(
        {"_id": candidate_id}, {"$set": {"status": "descartado"}}
    )


def approved_cases() -> list[dict]:
    """Casos aprobados en el formato de evals/hazmat_evals.json."""
    out = []
    for c in get_db()[CASES].find({}):
        case = {k: c[k] for k in ("level", "question", "keywords_all") if k in c}
        case["id"] = c["_id"]
        if c.get("pages"):
            case["pages"] = c["pages"]
        out.append(case)
    return out
