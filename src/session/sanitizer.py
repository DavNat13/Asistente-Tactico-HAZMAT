"""Validación de entradas hacia MongoDB.

Principio: los VALORES se guardan siempre con consultas parametrizadas (pymongo), por lo que el
texto del usuario no puede inyectar operadores. El riesgo real de NoSQL injection está en las
CLAVES (`$where`, `$ne`…) y en identificadores no validados; eso es lo que se controla aquí.
El XSS se controla al RENDERIZAR (src/ui/renderers), no bloqueando texto legítimo al guardar.
"""

import re
from typing import Any, ClassVar

from .validators import validate_role, validate_score

_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE
)
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_USERNAME_RE = re.compile(r"^[a-z0-9._-]{3,32}$")


class InputSanitizer:
    MAX_SESSION_ID_LENGTH: ClassVar[int] = 64
    MAX_MESSAGE_LENGTH: ClassVar[int] = 50000
    MAX_TITLE_LENGTH: ClassVar[int] = 200

    @classmethod
    def sanitize_string(cls, value: str, max_length: int = 10000) -> str:
        if not isinstance(value, str):
            raise TypeError(f"Expected string, got {type(value).__name__}")
        return _CONTROL.sub("", value).strip()[:max_length]

    @classmethod
    def sanitize_uuid(cls, value: str) -> str:
        if not isinstance(value, str):
            raise TypeError(f"Expected string, got {type(value).__name__}")
        value = value.strip()
        if len(value) > cls.MAX_SESSION_ID_LENGTH or not _UUID_RE.match(value):
            raise ValueError("Invalid UUID")
        return value.lower()

    @classmethod
    def sanitize_username(cls, value: str) -> str:
        value = (value or "").strip().lower()
        if not _USERNAME_RE.match(value):
            raise ValueError("Usuario inválido (3-32 caracteres: a-z, 0-9, . _ -)")
        return value

    @classmethod
    def sanitize_message_content(cls, content: str) -> str:
        return cls.sanitize_string(content, cls.MAX_MESSAGE_LENGTH)

    @classmethod
    def sanitize_title(cls, title: str) -> str:
        return cls.sanitize_string(title, cls.MAX_TITLE_LENGTH)

    @classmethod
    def sanitize_dict(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Rechaza claves con operadores MongoDB ($) o rutas (.) de forma recursiva."""
        if not isinstance(data, dict):
            return data
        clean: dict[str, Any] = {}
        for key, value in data.items():
            if not isinstance(key, str) or key.startswith("$") or "." in key:
                raise ValueError(f"Clave no permitida: {str(key)[:20]}")
            if isinstance(value, dict):
                clean[key] = cls.sanitize_dict(value)
            elif isinstance(value, list):
                clean[key] = [
                    cls.sanitize_dict(v) if isinstance(v, dict) else v for v in value
                ]
            elif isinstance(value, str):
                clean[key] = cls.sanitize_string(value)
            else:
                clean[key] = value
        return clean

    @classmethod
    def validate_role(cls, role: str) -> str:
        return validate_role(role)

    @classmethod
    def validate_score(cls, score: float) -> float:
        return validate_score(score)
