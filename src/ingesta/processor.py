"""Chunking, embeddings e índice estructurado de números UN."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from datetime import UTC, datetime

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config.settings import settings

_GUIDE_HEADINGS = (
    "PELIGROS POTENCIALES|SEGURIDAD PÚBLICA|ROPA PROTECTORA|EVACUACIÓN|RESPUESTA DE EMERGENCIA"
    "|DERRAME O FUGA|PRIMEROS AUXILIOS|INCENDIO O EXPLOSIÓN|A LA SALUD"
)
_FOOTER_RE = re.compile(
    r"\n?GRE2024\s*\n(?:GU[ÍI]A\s*\n\s*\d{3}\s*\n.+?\n)?\s*P[áa]gina\s+\d+\s*$",
    re.DOTALL,
)
_UN_RE = re.compile(r"(?<!\d)(\d{4})(?!\d)")

SECTION_LABELS = {
    "amarillas": "Páginas amarillas (índice por N° UN)",
    "azules": "Páginas azules (índice por nombre)",
    "tabla1": "Tabla 1 — Distancias de aislamiento inicial y acción protectora",
    "tabla2": "Tabla 2 — Materiales que reaccionan con agua",
    "tabla3": "Tabla 3 — Distancias para 6 gases tóxicos comunes",
    "general": "Sección general",
}


def normalize(text: str) -> str:
    t = unicodedata.normalize("NFKD", (text or "").lower())
    t = t.encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", t)).strip()


def get_text_splitter() -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        separators=[
            rf"\n(?=(?:{_GUIDE_HEADINGS})\b)",
            r"\n\n",
            r"\n(?=• )",
            r"\n",
            r" ",
        ],
        is_separator_regex=True,
        keep_separator=True,
    )


_embeddings_instance = None


def get_embeddings():
    """Modelo de embeddings local (singleton, CPU)."""
    global _embeddings_instance
    if _embeddings_instance is None:
        from langchain_huggingface import HuggingFaceEmbeddings

        _embeddings_instance = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
    return _embeddings_instance


def chunk_header(meta: dict) -> str:
    """Encabezado contextual que se antepone a cada chunk (mejora la recuperación y la cita)."""
    if meta.get("section") == "guia":
        return (
            f"{meta['source']} · GUÍA {meta['guide_number']} — {meta.get('guide_title', '')} "
            f"· Página {meta['page_label']}"
        )
    label = SECTION_LABELS.get(meta.get("section", "general"), "")
    if meta.get("source") != "GRE 2024":
        label = ""
    return " · ".join(
        p for p in (meta["source"], label, f"Página {meta['page_label']}") if p
    )


def split_documents(documents: list[Document], text_splitter=None) -> list[Document]:
    splitter = text_splitter or get_text_splitter()
    chunks: list[Document] = []
    for doc in documents:
        body = _FOOTER_RE.sub("", doc.page_content).strip()
        header = chunk_header(doc.metadata)
        for i, piece in enumerate(splitter.split_text(body)):
            piece = piece.strip()
            if len(piece) < 40:
                continue
            meta = dict(doc.metadata, chunk_index=i)
            chunks.append(Document(page_content=f"{header}\n{piece}", metadata=meta))
    print(f"Total de chunks generados: {len(chunks)}")
    return chunks


def chunk_id(meta: dict) -> str:
    """ID determinista del chunk (deduplicación en upserts). No es un uso criptográfico."""
    raw = f"{meta.get('file')}|{meta.get('page')}|{meta.get('chunk_index')}"
    return hashlib.sha1(raw.encode(), usedforsecurity=False).hexdigest()


def prepare_documents(
    chunks: list[Document], embeddings_model=None, batch_size: int = 64
) -> list[dict]:
    embeddings_model = embeddings_model or get_embeddings()
    now = datetime.now(tz=UTC).isoformat()
    vectors: list[list[float]] = []
    texts = [c.page_content for c in chunks]
    for start in range(0, len(texts), batch_size):
        vectors.extend(
            embeddings_model.embed_documents(texts[start : start + batch_size])
        )
        print(
            f"  embeddings {min(start + batch_size, len(texts))}/{len(texts)}",
            flush=True,
        )
    docs = []
    for chunk, vec in zip(chunks, vectors, strict=True):
        meta = dict(chunk.metadata)
        meta["un_numbers"] = sorted(set(_UN_RE.findall(chunk.page_content)))[:50]
        meta["ingestion_date"] = now
        meta["page_number"] = (
            int(meta["page_label"])
            if str(meta.get("page_label", "")).isdigit()
            else meta["page"]
        )
        docs.append(
            {
                "_id": chunk_id(meta),
                "text": chunk.page_content,
                "embedding": vec,
                "metadata": meta,
            }
        )
    return docs
