"""Configuración central (singleton). Todo parámetro sensible o ajustable viene del entorno."""

import itertools
import os
import threading

from dotenv import load_dotenv

load_dotenv()


def _clean(s: str) -> str:
    return s.strip().strip('"').strip("'")


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


def _env_bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes", "si")


class Settings:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_settings()
        return cls._instance

    def _init_settings(self):
        # --- Base de datos ---
        self.MONGODB_URI: str = os.getenv("MONGODB_URI", "")
        self.MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "hazmat_gre")
        self.MONGODB_COLLECTION_NAME: str = os.getenv(
            "MONGODB_COLLECTION_NAME", "gre_chunks"
        )
        self.VECTOR_INDEX_NAME: str = os.getenv("VECTOR_INDEX_NAME", "vector_index")
        self.MONGODB_TIMEOUT_MS: int = _env_int("MONGODB_TIMEOUT_MS", 8000)
        # --- Trazabilidad (LangSmith) ---
        self.LANGCHAIN_API_KEY: str = os.getenv("LANGCHAIN_API_KEY", "")
        self.LANGCHAIN_TRACING_V2: str = os.getenv("LANGCHAIN_TRACING_V2", "true")
        self.LANGCHAIN_PROJECT: str = os.getenv(
            "LANGCHAIN_PROJECT", "Bomberos-HAZMAT-RAG"
        )
        # --- Modelos ---
        self.EMBEDDING_MODEL: str = os.getenv(
            "EMBEDDING_MODEL",
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        )
        self.EMBEDDING_DIMENSIONS: int = _env_int("EMBEDDING_DIMENSIONS", 384)
        self.LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-3.6-flash")
        self.LLM_TEMPERATURE: float = _env_float("LLM_TEMPERATURE", 0.1)
        self.LLM_TIMEOUT_S: int = _env_int("LLM_TIMEOUT_S", 30)
        # Cadena de respaldo ante sobrecarga (503) o timeout del modelo principal
        self.LLM_FALLBACK_MODELS: list[str] = [
            m.strip()
            for m in os.getenv(
                "LLM_FALLBACK_MODELS", "gemini-3.5-flash-lite,gemini-3.1-flash-lite"
            ).split(",")
            if m.strip()
        ]
        self.MODEL_COOLDOWN_S: int = _env_int("MODEL_COOLDOWN_S", 120)

        # --- Pool de API keys (rotación thread-safe) ---
        keys = [
            _clean(k) for k in os.getenv("GEMINI_API_KEYS", "").split(",") if _clean(k)
        ]
        if not keys:  # compatibilidad hacia atrás
            single = _clean(
                os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", "")
            )
            keys = [single] if single else []
        self.API_KEYS: list[str] = keys
        self.GOOGLE_API_KEY: str = keys[0] if keys else ""
        self._key_cycle = itertools.cycle(keys) if keys else None
        self._key_lock = threading.Lock()
        self.LLM_MAX_RETRIES: int = _env_int("LLM_MAX_RETRIES", max(len(keys), 1))

        # --- Ingesta y recuperación ---
        self.CHUNK_SIZE: int = _env_int("CHUNK_SIZE", 1200)
        self.CHUNK_OVERLAP: int = _env_int("CHUNK_OVERLAP", 200)
        self.RETRIEVAL_TOP_K: int = _env_int("RETRIEVAL_TOP_K", 6)
        self.RETRIEVAL_MIN_SCORE: float = _env_float("RETRIEVAL_MIN_SCORE", 0.35)

        # --- Agente ---
        self.AGENT_HISTORY_MESSAGES: int = _env_int("AGENT_HISTORY_MESSAGES", 10)
        self.TOOL_BUDGET = {"low": 0, "medium": 2, "high": 5}
        self.AGENT_RECURSION_LIMIT: int = _env_int("AGENT_RECURSION_LIMIT", 16)
        self.ROUTER_USE_LLM: bool = _env_bool("ROUTER_USE_LLM", False)

        # --- Seguridad ---
        self.MAX_QUERY_CHARS: int = _env_int("MAX_QUERY_CHARS", 2000)
        self.RATE_LIMIT_PER_MIN: int = _env_int("RATE_LIMIT_PER_MIN", 12)
        self.GUARDRAIL_LLM: bool = _env_bool("GUARDRAIL_LLM", True)
        # Modelo liviano para el clasificador de seguridad (rápido; no espera al principal)
        self.GUARDRAIL_MODEL: str = os.getenv(
            "GUARDRAIL_MODEL", "gemini-3.5-flash-lite"
        )
        self.AUTH_ENABLED: bool = _env_bool("AUTH_ENABLED", True)
        self.LOGIN_MAX_ATTEMPTS: int = _env_int("LOGIN_MAX_ATTEMPTS", 5)
        self.LOGIN_LOCK_MINUTES: int = _env_int("LOGIN_LOCK_MINUTES", 15)
        # Sal para seudonimizar usuarios en la telemetría
        self.TELEMETRY_SALT: str = os.getenv("TELEMETRY_SALT", "hazmat-telemetry")
        # Clave HMAC de los códigos de verificación (vacía → clave aleatoria por proceso)
        self.OTP_SECRET: str = os.getenv("OTP_SECRET", "")

        # --- Sesiones / retención de datos ---
        self.SESSION_COLLECTION_NAME: str = os.getenv(
            "SESSION_COLLECTION_NAME", "sessions"
        )
        self.SESSION_MAX_HISTORY_MESSAGES: int = _env_int(
            "SESSION_MAX_HISTORY_MESSAGES", 100
        )
        self.SESSION_TTL_DAYS: int = _env_int("SESSION_TTL_DAYS", 90)
        self.TELEMETRY_TTL_DAYS: int = _env_int("TELEMETRY_TTL_DAYS", 180)

        self._validate_required()

    def get_next_api_key(self) -> str:
        if self._key_cycle is None:
            raise ValueError("No hay API keys configuradas (GEMINI_API_KEYS)")
        with self._key_lock:  # itertools.cycle no es thread-safe
            return next(self._key_cycle)

    def _validate_required(self):
        missing = []
        if not self.API_KEYS:
            missing.append("GEMINI_API_KEYS (o GOOGLE_API_KEY)")
        if not self.MONGODB_URI:
            missing.append("MONGODB_URI")
        if missing:
            raise ValueError(
                f"Variables de entorno requeridas faltantes: {', '.join(missing)}"
            )


settings = Settings()
