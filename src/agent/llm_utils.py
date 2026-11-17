"""Utilidades del cliente LLM: clasificación de errores y normalización de contenido.

Estrategia de recuperación según la causa del error:
- "key"   (429 cuota, 403 llave inválida)      → rotar a la siguiente API key.
- "model" (503 sobrecarga, timeout, 404 modelo) → cambiar al siguiente modelo de respaldo
                                                  (rotar llaves no sirve: el problema es del modelo).
- None    (400, argumentos inválidos, otros)    → relanzar: reintentar ocultaría un bug.
"""

from __future__ import annotations

_KEY_MARKERS = (
    "429",
    "resource_exhausted",
    "resourceexhausted",
    "quota",
    "rate limit",
    "api key not valid",
    "api_key_invalid",
    "permission_denied",
    "permissiondenied",
    "403",
)
_MODEL_MARKERS = (
    "503",
    "unavailable",
    "overloaded",
    "high demand",
    "timeout",
    "timed out",
    "deadline",
    "modelnotfound",
    "model not found",
    "404",
)


def failure_kind(exc: Exception) -> str | None:
    text = f"{type(exc).__name__}: {exc}".lower()
    if any(m in text for m in _MODEL_MARKERS):
        return "model"
    if any(m in text for m in _KEY_MARKERS):
        return "key"
    return None


def is_retryable(exc: Exception) -> bool:
    return failure_kind(exc) is not None


def content_text(content) -> str:
    """Normaliza el contenido de un AIMessage (str o lista de partes) a texto plano."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            p.get("text", "") if isinstance(p, dict) else str(p) for p in content
        )
    return str(content or "")
