import itertools
import os
import threading

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
        self.MONGODB_COLLECTION_NAME: str = os.getenv(
            "MONGODB_COLLECTION_NAME", "gre_chunks"
        )
        self.LANGCHAIN_API_KEY: str = os.getenv("LANGCHAIN_API_KEY", "")
        self.LANGCHAIN_TRACING_V2: str = os.getenv("LANGCHAIN_TRACING_V2", "true")
        self.LANGCHAIN_PROJECT: str = os.getenv(
            "LANGCHAIN_PROJECT", "Bomberos-HAZMAT-RAG"
        )
        self.EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
        self.EMBEDDING_DIMENSIONS: int = 384
        self.LLM_MODEL: str = "gemini-3.6-flash"
        self.LLM_TEMPERATURE: float = 0.1

        # --- Pool de API keys (rotación thread-safe) ---
        def _clean(s: str) -> str:
            return s.strip().strip('"').strip("'")

        _raw_keys = os.getenv("GEMINI_API_KEYS", "")
        keys = [_clean(k) for k in _raw_keys.split(",") if _clean(k)]
        if not keys:  # compat hacia atrás
            _single = _clean(os.getenv("GEMINI_API_KEY") or self.GOOGLE_API_KEY)
            keys = [_single] if _single else []
        self.API_KEYS: list[str] = keys
        self._key_cycle = itertools.cycle(keys)
        self._key_lock = threading.Lock()
        self.LLM_MAX_RETRIES: int = int(
            os.getenv("LLM_MAX_RETRIES", str(max(len(keys), 1)))
        )

        self.CHUNK_SIZE: int = 1000
        self.CHUNK_OVERLAP: int = 150
        self.RETRIEVAL_TOP_K: int = 8
        self.RETRIEVAL_MIN_SCORE: float = 0.50
        self.AGENT_ENABLED: bool = True

        # Session Management
        self.SESSION_COLLECTION_NAME: str = os.getenv(
            "SESSION_COLLECTION_NAME", "sessions"
        )
        self.SESSION_MAX_HISTORY_MESSAGES: int = int(
            os.getenv("SESSION_MAX_HISTORY_MESSAGES", "100")
        )
        self.SESSION_TTL_DAYS: int = int(os.getenv("SESSION_TTL_DAYS", "90"))

        self._validate_required()

    def get_next_api_key(self) -> str:
        with self._key_lock:  # itertools.cycle no es thread-safe
            return next(self._key_cycle)

    def _validate_required(self):
        required = {
            "GOOGLE_API_KEY": self.GOOGLE_API_KEY,
            "MONGODB_URI": self.MONGODB_URI,
        }
        missing = [k for k, v in required.items() if not v]
        if missing:
            raise ValueError(
                f"Variables de entorno requeridas faltantes: {', '.join(missing)}"
            )


settings = Settings()
