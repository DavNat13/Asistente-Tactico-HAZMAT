"""Ingesta de PDFs → MongoDB Atlas (chunks + embeddings + índice UN + índices de búsqueda).

Uso:
    python -m src.ingesta.ingest --data --create-index            # todos los PDFs de data/
    python -m src.ingesta.ingest --data --clear --create-index    # re-ingesta completa
    python -m src.ingesta.ingest --pdf data/GRE_2024.pdf
"""

from __future__ import annotations

import argparse

from pymongo import MongoClient, ReplaceOne

from src.config.settings import settings
from src.ingesta.indexes import create_indexes, wait_for_vector_index
from src.ingesta.loaders import load_directory, load_single_pdf
from src.ingesta.processor import prepare_documents, split_documents
from src.ingesta.un_index import build_un_index

UN_INDEX_COLLECTION = "un_index"


class PDFIngester:
    def __init__(self, collection: str | None = None):
        self.client = MongoClient(
            settings.MONGODB_URI, serverSelectionTimeoutMS=settings.MONGODB_TIMEOUT_MS
        )
        self.db = self.client[settings.MONGODB_DB_NAME]
        self.collection = self.db[collection or settings.MONGODB_COLLECTION_NAME]
        self.un_index = self.db[UN_INDEX_COLLECTION]

    def _upsert(self, docs: list[dict]) -> int:
        if not docs:
            return 0
        ops = [ReplaceOne({"_id": d["_id"]}, d, upsert=True) for d in docs]
        for start in range(0, len(ops), 200):
            self.collection.bulk_write(ops[start : start + 200], ordered=False)
        print(f"Upsert de {len(docs)} chunks en '{self.collection.name}'.")
        return len(docs)

    def _ingest(self, documents) -> int:
        if not documents:
            return 0
        entries = build_un_index(documents)
        if entries:
            self.un_index.bulk_write(
                [ReplaceOne({"_id": e["_id"]}, e, upsert=True) for e in entries],
                ordered=False,
            )
            self.un_index.create_index("names_norm")
        chunks = split_documents(documents)
        return self._upsert(prepare_documents(chunks))

    def ingest_pdf(self, pdf_path: str) -> int:
        return self._ingest(load_single_pdf(pdf_path))

    def ingest_directory(self, directory: str | None = None) -> int:
        return self._ingest(load_directory(directory))

    def clear_collection(self) -> None:
        self.collection.delete_many({})
        self.un_index.delete_many({})
        print("Colecciones de chunks e índice UN limpiadas.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingesta de PDFs para HAZMAT RAG")
    parser.add_argument("--pdf", type=str, help="Ruta local al archivo PDF")
    parser.add_argument(
        "--data", action="store_true", help="Ingerir todos los PDFs de data/"
    )
    parser.add_argument(
        "--collection", type=str, help="Colección destino (por defecto la de .env)"
    )
    parser.add_argument(
        "--clear", action="store_true", help="Limpiar colección antes de ingerir"
    )
    parser.add_argument(
        "--create-index", action="store_true", help="Crear/actualizar índices"
    )
    args = parser.parse_args()

    ingester = PDFIngester(args.collection)
    if args.clear:
        ingester.clear_collection()
    if args.pdf:
        ingester.ingest_pdf(args.pdf)
    elif args.data:
        ingester.ingest_directory()
    if args.create_index:
        create_indexes(ingester.collection)
        wait_for_vector_index(ingester.collection)
    if not (args.pdf or args.data or args.create_index or args.clear):
        parser.print_help()


if __name__ == "__main__":
    main()
