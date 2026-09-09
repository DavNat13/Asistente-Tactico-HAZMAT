from pymongo import MongoClient
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import settings
from src.ingesta.loaders import load_single_pdf, load_directory, load_from_github
from src.ingesta.processor import get_text_splitter, get_embeddings, split_documents, prepare_documents


class PDFIngester:
    def __init__(self):
        self.embeddings = get_embeddings()
        self.client = MongoClient(settings.MONGODB_URI)
        self.db = self.client[settings.MONGODB_DB_NAME]
        self.collection = self.db[settings.MONGODB_COLLECTION_NAME]
        self.text_splitter = get_text_splitter()

    def _insert_documents(self, docs_to_insert):
        if docs_to_insert:
            self.collection.insert_many(docs_to_insert)
            print(f"Insertados {len(docs_to_insert)} chunks en MongoDB.")
        return len(docs_to_insert)

    def ingest_pdf(self, pdf_path: str) -> int:
        documents = load_single_pdf(pdf_path)
        chunks = split_documents(documents, self.text_splitter)
        return self._insert_documents(prepare_documents(chunks, self.embeddings))

    def ingest_directory(self, directory: str = None) -> int:
        documents = load_directory(directory)
        if not documents:
            return 0
        chunks = split_documents(documents, self.text_splitter)
        return self._insert_documents(prepare_documents(chunks, self.embeddings))

    def ingest_from_github(self, repo_url: str) -> int:
        documents = load_from_github(repo_url)
        chunks = split_documents(documents, self.text_splitter)
        return self._insert_documents(prepare_documents(chunks, self.embeddings))

    def create_vector_index(self):
        index_name = "vector_index"
        if index_name in self.collection.index_information():
            print(f"Índice '{index_name}' ya existe.")
            return
        self.collection.create_index(
            [("embedding", "vector")],
            name=index_name,
            vectorOptions={
                "dimensions": settings.EMBEDDING_DIMENSIONS,
                "similarity": "cosine"
            }
        )
        print(f"Índice vectorial '{index_name}' creado exitosamente.")

    def clear_collection(self):
        self.collection.delete_many({})
        print("Colección limpiada exitosamente.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Ingesta de PDFs para HAZMAT RAG")
    parser.add_argument("--pdf", type=str, help="Ruta local al archivo PDF")
    parser.add_argument("--data", action="store_true", help="Cargar todos los PDFs del directorio data/")
    parser.add_argument("--github", type=str, help="URL del repositorio GitHub")
    parser.add_argument("--clear", action="store_true", help="Limpiar colección antes de ingerir")
    parser.add_argument("--create-index", action="store_true", help="Crear índice vectorial")
    args = parser.parse_args()
    ingester = PDFIngester()
    if args.clear:
        ingester.clear_collection()
    if args.create_index:
        ingester.create_vector_index()
    if args.pdf:
        ingester.ingest_pdf(args.pdf)
    elif args.data:
        ingester.ingest_directory()
    elif args.github:
        ingester.ingest_from_github(args.github)
    else:
        print("Especifique --pdf, --data o --github para ingerir documentos.")
