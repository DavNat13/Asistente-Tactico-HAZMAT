"""Primitivas de búsqueda: vectorial ($vectorSearch), léxica ($text en español) y fusión RRF."""

from __future__ import annotations

import logging

from src.config.settings import settings
from src.ingesta.processor import get_embeddings

log = logging.getLogger("hazmat.retrieval")

RRF_K = 60


def vector_search(
    collection, query: str, k: int, filters: dict | None = None
) -> list[dict]:
    stage: dict = {
        "index": settings.VECTOR_INDEX_NAME,
        "path": "embedding",
        "queryVector": get_embeddings().embed_query(query),
        "numCandidates": k * 15,
        "limit": k,
    }
    if filters:
        stage["filter"] = filters
    pipeline = [
        {"$vectorSearch": stage},
        {
            "$project": {
                "_id": 1,
                "text": 1,
                "metadata": 1,
                "score": {"$meta": "vectorSearchScore"},
            }
        },
    ]
    res = list(collection.aggregate(pipeline))
    return [r for r in res if r.get("score", 0) >= settings.RETRIEVAL_MIN_SCORE]


def text_search(
    collection, query: str, k: int, source: str | None = None
) -> list[dict]:
    match: dict = {"$text": {"$search": query, "$language": "spanish"}}
    if source:
        match["metadata.source"] = source
    try:
        cursor = (
            collection.find(
                match, {"text": 1, "metadata": 1, "tscore": {"$meta": "textScore"}}
            )
            .sort([("tscore", {"$meta": "textScore"})])
            .limit(k)
        )
        return list(cursor)
    except Exception as e:  # noqa: BLE001 — sin índice de texto: se degrada a solo vector
        log.warning("text_search no disponible: %s", e)
        return []


def rrf_fuse(vec: list[dict], lex: list[dict], k: int) -> list[dict]:
    """Reciprocal Rank Fusion. `match` indica el origen: vector | lexico | hibrido."""
    fused: dict[str, dict] = {}
    for rank, doc in enumerate(vec):
        item = fused.setdefault(str(doc["_id"]), {**doc, "rrf": 0.0, "match": "vector"})
        item["rrf"] += 1 / (RRF_K + rank)
    for rank, doc in enumerate(lex):
        key = str(doc["_id"])
        if key in fused:
            fused[key]["match"] = "hibrido"
        else:
            fused[key] = {**doc, "rrf": 0.0, "match": "lexico", "score": None}
        fused[key]["rrf"] += 1 / (RRF_K + rank)

    ranked = sorted(fused.values(), key=lambda d: d["rrf"], reverse=True)[:k]
    best = ranked[0]["rrf"] if ranked else 1
    for d in ranked:
        d["_id"] = str(d["_id"])
        d.pop("tscore", None)
        if d.get("score") is None:  # léxico puro: score relativo al mejor RRF (máx 0.8)
            d["score"] = min(1.0, d["rrf"] / best) * 0.8
        d["score"] = round(float(d["score"]), 3)
    return ranked
