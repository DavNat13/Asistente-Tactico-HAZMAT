"""Configuración común: raíz del proyecto en sys.path y variables mínimas para importar settings."""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("GEMINI_API_KEYS", "test-key")
os.environ.setdefault("MONGODB_URI", "mongodb://localhost:27017/test")
os.environ.setdefault("GUARDRAIL_LLM", "false")
