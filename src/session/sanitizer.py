import re
from typing import Any, ClassVar

from .validators import validate_role, validate_score


class InputSanitizer:
    NOSQL_INJECTION_PATTERNS: ClassVar[list] = [
        re.compile(r"\$where", re.IGNORECASE),
        re.compile(r"\$regex", re.IGNORECASE),
        re.compile(r"\$ne", re.IGNORECASE),
        re.compile(r"\$gt", re.IGNORECASE),
        re.compile(r"\$lt", re.IGNORECASE),
        re.compile(r"\$exists", re.IGNORECASE),
        re.compile(r"\$in", re.IGNORECASE),
        re.compile(r"\$nin", re.IGNORECASE),
        re.compile(r"\$and", re.IGNORECASE),
        re.compile(r"\$or", re.IGNORECASE),
        re.compile(r"function\s*\(", re.IGNORECASE),
        re.compile(r"ObjectId\s*\(", re.IGNORECASE),
        re.compile(r"ISODate\s*\(", re.IGNORECASE),
    ]
    XSS_PATTERNS: ClassVar[list] = [
        re.compile(r"<script", re.IGNORECASE),
        re.compile(r"javascript:", re.IGNORECASE),
        re.compile(r"on(?:click|load|error|mouse\w+)\s*=", re.IGNORECASE),
        re.compile(r"<iframe", re.IGNORECASE),
        re.compile(r"<object", re.IGNORECASE),
        re.compile(r"<embed", re.IGNORECASE),
    ]
    MAX_SESSION_ID_LENGTH = 64
    MAX_MESSAGE_LENGTH = 50000
    MAX_TITLE_LENGTH = 200

    @classmethod
    def sanitize_string(cls, value: str, max_length: int = 10000) -> str:
        if not isinstance(value, str):
            raise TypeError(f"Expected string, got {type(value).__name__}")
        value = value.strip()[:max_length]
        for pattern in cls.NOSQL_INJECTION_PATTERNS:
            if pattern.search(value):
                raise ValueError("Input contains dangerous characters")
        for pattern in cls.XSS_PATTERNS:
            if pattern.search(value):
                raise ValueError("Input contains dangerous HTML")
        return value

    @classmethod
    def sanitize_uuid(cls, value: str) -> str:
        if not isinstance(value, str):
            raise TypeError(f"Expected string, got {type(value).__name__}")
        value = value.strip()
        uuid_re = re.compile(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-"
            r"[0-9a-f]{4}-[0-9a-f]{12}$",
            re.IGNORECASE,
        )
        if not uuid_re.match(value):
            raise ValueError(f"Invalid UUID: {value[:20]}...")
        if len(value) > cls.MAX_SESSION_ID_LENGTH:
            raise ValueError("UUID exceeds maximum length")
        return value.lower()

    @classmethod
    def sanitize_message_content(cls, content: str) -> str:
        return cls.sanitize_string(content, cls.MAX_MESSAGE_LENGTH)

    @classmethod
    def sanitize_title(cls, title: str) -> str:
        return cls.sanitize_string(title, cls.MAX_TITLE_LENGTH)

    @classmethod
    def sanitize_dict(cls, data: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(data, dict):
            return data
        sanitized = {}
        for key, value in data.items():
            if key.startswith("$"):
                raise ValueError(f"Key '{key}' contains MongoDB operator")
            if isinstance(value, str):
                sanitized[key] = cls.sanitize_string(value)
            elif isinstance(value, dict):
                sanitized[key] = cls.sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    cls.sanitize_dict(v)
                    if isinstance(v, dict)
                    else cls.sanitize_string(v)
                    if isinstance(v, str)
                    else v
                    for v in value
                ]
            else:
                sanitized[key] = value
        return sanitized

    @classmethod
    def validate_role(cls, role: str) -> str:
        return validate_role(role)

    @classmethod
    def validate_score(cls, score: float) -> float:
        return validate_score(score)
