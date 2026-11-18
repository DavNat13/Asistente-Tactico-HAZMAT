"""Índices de MongoDB Atlas: vectorial (con filtros), texto en español y metadatos."""

from __future__ import annotations

import time

from pymongo.errors import OperationFailure
from pymongo.operations import SearchIndexModel

from src.config.settings import settings


def create_indexes(collection) -> None:
    """Índice vectorial (con campos filtrables) + índice de texto para búsqueda léxica."""
    definition = {
        "fields": [
            {
                "type": "vector",
                "path": "embedding",
                "numDimensions": settings.EMBEDDING_DIMENSIONS,
                "similarity": "cosine",
            },
            {"type": "filter", "path": "metadata.source"},
            {"type": "filter", "path": "metadata.section"},
            {"type": "filter", "path": "metadata.guide_number"},
        ]
    }
    name = settings.VECTOR_INDEX_NAME
    existing = {ix["name"] for ix in collection.list_search_indexes()}
    try:
        if name in existing:
            collection.update_search_index(name, definition)
            print(f"Índice vectorial '{name}' actualizado.")
        else:
            model = SearchIndexModel(
                definition=definition, name=name, type="vectorSearch"
            )
            collection.create_search_index(model)
            print(f"Índice vectorial '{name}' creado.")
    except OperationFailure as e:
        print(f"No se pudo crear/actualizar el índice vectorial: {e}")

    collection.create_index(
        [("text", "text")],
        default_language="spanish",
        name="text_es",
        language_override="_lang",
    )
    collection.create_index("metadata.guide_number")
    collection.create_index("metadata.un_numbers")
    print("Índices de texto y metadatos listos.")


def wait_for_vector_index(collection, timeout_s: int = 300) -> bool:
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        for ix in collection.list_search_indexes(settings.VECTOR_INDEX_NAME):
            if ix.get("queryable") and ix.get("status") == "READY":
                print("Índice vectorial READY.")
                return True
        time.sleep(5)
    print("Timeout esperando el índice vectorial.")
    return False
