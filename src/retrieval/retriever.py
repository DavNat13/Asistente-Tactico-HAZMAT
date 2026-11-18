"""Fachada de recuperación sobre MongoDB Atlas.

- hybrid_search  : vector + léxica fusionadas con RRF (ver search.py).
- lookup_un      : búsqueda exacta por N° UN (índice de páginas amarillas + Tabla 1).
- search_material: búsqueda por nombre de material (sin tildes; coincidencia por palabra completa).
- get_guide      : todos los chunks de una guía naranja, en orden.

Conexión perezosa: importar este módulo no abre sockets (la app arranca aunque Mongo no responda).
"""

from __future__ import annotations

import logging
import re
import threading

from langsmith import traceable
from pymongo import MongoClient

from src.config.settings import settings
from src.ingesta.processor import normalize
from src.retrieval.search import rrf_fuse, text_search, vector_search

log = logging.getLogger("hazmat.retrieval")

UN_INDEX_COLLECTION = "un_index"


class Retriever:
    def __init__(self):
        self._client: MongoClient | None = None
        self._lock = threading.Lock()

    @property
    def client(self) -> MongoClient:
        if self._client is None:
            with self._lock:
                if self._client is None:
                    self._client = MongoClient(
                        settings.MONGODB_URI,
                        serverSelectionTimeoutMS=settings.MONGODB_TIMEOUT_MS,
                    )
        return self._client

    @property
    def db(self):
        return self.client[settings.MONGODB_DB_NAME]

    @property
    def collection(self):
        return self.db[settings.MONGODB_COLLECTION_NAME]

    @traceable(name="hazmat_hybrid_search", run_type="retriever")
    def hybrid_search(
        self, query: str, k: int | None = None, source: str | None = None
    ) -> list[dict]:
        k = k or settings.RETRIEVAL_TOP_K
        filters = {"metadata.source": {"$eq": source}} if source else None
        vec = vector_search(self.collection, query, k * 2, filters)
        lex = text_search(self.collection, query, k * 2, source)
        ranked = rrf_fuse(vec, lex, k)
        log.info(
            "hybrid_search q=%r vec=%d lex=%d out=%d",
            query[:60],
            len(vec),
            len(lex),
            len(ranked),
        )
        return ranked

    @traceable(name="hazmat_lookup_un", run_type="retriever")
    def lookup_un(self, un: str) -> dict | None:
        un = re.sub(r"\D", "", un or "")[:4]
        if len(un) != 4:
            return None
        return self.db[UN_INDEX_COLLECTION].find_one({"_id": un}, {"names_norm": 0})

    @traceable(name="hazmat_search_material", run_type="retriever")
    def search_material(self, name: str, limit: int = 5) -> list[dict]:
        q = normalize(name)
        if len(q) < 3:
            return []
        words = [re.escape(t) for t in q.split() if len(t) > 2] or [re.escape(q)]
        query = {"$and": [{"names_norm": {"$regex": rf"(^| ){w}( |$)"}} for w in words]}
        docs = list(self.db[UN_INDEX_COLLECTION].find(query).limit(limit * 6))

        def rank(d):  # 0 = nombre exacto, 1 = empieza igual, 2 = contiene
            names = d.get("names_norm", [])
            return 0 if q in names else 1 if any(n.startswith(q) for n in names) else 2

        docs = sorted(docs, key=rank)[:limit]
        for d in docs:
            d.pop("names_norm", None)
        return docs

    @traceable(name="hazmat_get_guide", run_type="retriever")
    def get_guide(self, guide_number: str) -> list[dict]:
        g = re.sub(r"\D", "", guide_number or "")[:3]
        if not re.fullmatch(r"1[1-7]\d", g):
            return []
        cursor = self.collection.find(
            {"metadata.guide_number": g}, {"embedding": 0}
        ).sort([("metadata.page", 1), ("metadata.chunk_index", 1)])
        docs = []
        for d in cursor:
            d["_id"], d["score"], d["match"] = str(d["_id"]), 1.0, "guia"
            docs.append(d)
        return docs

    def ping(self) -> bool:
        try:
            self.client.admin.command("ping")
            return True
        except Exception:  # noqa: BLE001
            return False

    def get_collection_stats(self) -> dict:
        return {
            "total_chunks": self.collection.estimated_document_count(),
            "un_numbers": self.db[UN_INDEX_COLLECTION].estimated_document_count(),
            "collection": settings.MONGODB_COLLECTION_NAME,
        }


retriever = Retriever()
