import os
import sys
from datetime import datetime, timezone

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import settings


def get_text_splitter():
    return RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        length_function=len,
        is_separator_regex=False,
    )


_embeddings_instance = None


def get_embeddings():
    global _embeddings_instance
    if _embeddings_instance is None:
        _embeddings_instance = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
    return _embeddings_instance


def split_documents(documents: list, text_splitter) -> list:
    chunks = text_splitter.split_documents(documents)
    print(f"Total de chunks generados: {len(chunks)}")
    return chunks


def prepare_documents(chunks: list, embeddings_model) -> list:
    docs_to_insert = []
    for i, chunk in enumerate(chunks):
        source_file = chunk.metadata.get("source", "unknown.pdf")
        source_filename = os.path.basename(source_file)
        page_number = chunk.metadata.get("page_number", i + 1)

        embedding = embeddings_model.embed_query(chunk.page_content)

        doc = {
            "chunk_id": i,
            "text": chunk.page_content,
            "embedding": embedding,
            "metadata": {
                "source": source_filename,
                "page_number": page_number,
                "ingestion_date": datetime.now(tz=timezone.utc).isoformat(),
                "total_chunks": len(chunks),
            },
        }
        docs_to_insert.append(doc)

    return docs_to_insert
