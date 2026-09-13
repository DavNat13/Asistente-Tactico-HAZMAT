from pymongo import MongoClient
from langsmith import traceable
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import settings
from src.ingesta.processor import get_embeddings


class Retriever:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if Retriever._initialized:
            return

        self.embeddings = get_embeddings()
        self.client = MongoClient(settings.MONGODB_URI)
        self.db = self.client[settings.MONGODB_DB_NAME]
        self.collection = self.db[settings.MONGODB_COLLECTION_NAME]
        self.index_name = "vector_index"
        Retriever._initialized = True

    @traceable(name="hazmat_retrieval")
    def retrieve(self, query: str, top_k: int = None, min_score: float = None) -> list[dict]:
        if top_k is None:
            top_k = settings.RETRIEVAL_TOP_K
        if min_score is None:
            min_score = settings.RETRIEVAL_MIN_SCORE

        query_embedding = self.embeddings.embed_query(query)

        pipeline = [
            {
                "$vectorSearch": {
                    "index": self.index_name,
                    "path": "embedding",
                    "queryVector": query_embedding,
                    "numCandidates": top_k * 10,
                    "limit": top_k,
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "text": 1,
                    "metadata": 1,
                    "score": {"$meta": "vectorSearchScore"},
                }
            }
        ]

        results = list(self.collection.aggregate(pipeline))

        filtered_results = [
            r for r in results
            if r.get("score", 0) >= min_score
        ]

        print(f"Query: {query[:50]}...")
        print(f"Results before filter: {len(results)}, after filter: {len(filtered_results)}")

        return filtered_results

    def get_collection_stats(self) -> dict:
        total_docs = self.collection.count_documents({})
        return {
            "total_chunks": total_docs,
            "database": settings.MONGODB_DB_NAME,
            "collection": settings.MONGODB_COLLECTION_NAME
        }


retriever = Retriever()
