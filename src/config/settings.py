import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_settings()
        return cls._instance

    def _init_settings(self):
        self.GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
        self.MONGODB_URI: str = os.getenv("MONGODB_URI", "")
        self.MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "hazmat_gre")
        self.MONGODB_COLLECTION_NAME: str = os.getenv("MONGODB_COLLECTION_NAME", "gre_chunks")
        self.LANGCHAIN_API_KEY: str = os.getenv("LANGCHAIN_API_KEY", "")
        self.LANGCHAIN_TRACING_V2: str = os.getenv("LANGCHAIN_TRACING_V2", "true")
        self.LANGCHAIN_PROJECT: str = os.getenv("LANGCHAIN_PROJECT", "Bomberos-HAZMAT-RAG")
        self.EMBEDDING_MODEL: str = "models/embedding-001"
        self.EMBEDDING_DIMENSIONS: int = 768
        self.LLM_MODEL: str = "gemini-1.5-flash"
        self.LLM_TEMPERATURE: float = 0.1
        self.CHUNK_SIZE: int = 1000
        self.CHUNK_OVERLAP: int = 150
        self.RETRIEVAL_TOP_K: int = 4
        self.RETRIEVAL_MIN_SCORE: float = 0.75


settings = Settings()
