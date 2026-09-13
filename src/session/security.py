"""
Input sanitization and security utilities for session management.

Prevents NoSQL injection, XSS, and validates all inputs
before they reach the database layer.
"""

import re
from typing import Any


class InputSanitizer:
    """Sanitizes user inputs to prevent injection attacks."""

    # Patterns that indicate injection attempts
    NOSQL_INJECTION_PATTERNS = [
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

    XSS_PATTERNS = [
        re.compile(r"<script", re.IGNORECASE),
        re.compile(r"javascript:", re.IGNORECASE),
        re.compile(r"on\w+\s*=", re.IGNORECASE),
        re.compile(r"<iframe", re.IGNORECASE),
        re.compile(r"<object", re.IGNORECASE),
        re.compile(r"<embed", re.IGNORECASE),
    ]

    # Maximum allowed lengths
    MAX_SESSION_ID_LENGTH = 64
    MAX_THREAD_ID_LENGTH = 64
    MAX_MESSAGE_LENGTH = 50000
    MAX_TITLE_LENGTH = 200

    @classmethod
    def sanitize_string(cls, value: str, max_length: int = 10000) -> str:
        """Sanitize a string input by removing dangerous patterns."""
        if not isinstance(value, str):
            raise ValueError(f"Expected string, got {type(value).__name__}")

        # Strip and limit length
        value = value.strip()[:max_length]

        # Check for NoSQL injection patterns
        for pattern in cls.NOSQL_INJECTION_PATTERNS:
            if pattern.search(value):
                raise ValueError(
                    "Input contains potentially dangerous characters"
                )

        # Check for XSS patterns
        for pattern in cls.XSS_PATTERNS:
            if pattern.search(value):
                raise ValueError(
                    "Input contains potentially dangerous HTML"
                )

        return value

    @classmethod
    def sanitize_uuid(cls, value: str) -> str:
        """Validate and sanitize a UUID string."""
        if not isinstance(value, str):
            raise ValueError(f"Expected string, got {type(value).__name__}")

        value = value.strip()

        # UUID format: 8-4-4-4-12 hex characters
        uuid_pattern = re.compile(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
            re.IGNORECASE,
        )

        if not uuid_pattern.match(value):
            raise ValueError(f"Invalid UUID format: {value[:20]}...")

        if len(value) > cls.MAX_SESSION_ID_LENGTH:
            raise ValueError("UUID exceeds maximum allowed length")

        return value.lower()

    @classmethod
    def sanitize_message_content(cls, content: str) -> str:
        """Sanitize message content with appropriate length limits."""
        return cls.sanitize_string(content, cls.MAX_MESSAGE_LENGTH)

    @classmethod
    def sanitize_title(cls, title: str) -> str:
        """Sanitize a title string."""
        return cls.sanitize_string(title, cls.MAX_TITLE_LENGTH)

    @classmethod
    def sanitize_dict(cls, data: dict[str, Any]) -> dict[str, Any]:
        """
        Recursively sanitize dictionary values.

        Prevents MongoDB operator injection in nested documents.
        """
        if not isinstance(data, dict):
            return data

        sanitized = {}
        for key, value in data.items():
            # Remove any keys starting with $
            if key.startswith("$"):
                raise ValueError(
                    f"Key '{key}' contains MongoDB operator"
                )

            if isinstance(value, str):
                sanitized[key] = cls.sanitize_string(value)
            elif isinstance(value, dict):
                sanitized[key] = cls.sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    cls.sanitize_dict(v) if isinstance(v, dict)
                    else cls.sanitize_string(v) if isinstance(v, str)
                    else v
                    for v in value
                ]
            else:
                sanitized[key] = value

        return sanitized

    @classmethod
    def validate_role(cls, role: str) -> str:
        """Validate message role is one of allowed values."""
        allowed_roles = {"user", "assistant", "system"}
        role = role.strip().lower()
        if role not in allowed_roles:
            raise ValueError(
                f"Invalid role '{role}'. Must be one of: {allowed_roles}"
            )
        return role

    @classmethod
    def validate_score(cls, score: float) -> float:
        """Validate relevance score is within 0-1 range."""
        if not isinstance(score, (int, float)):
            raise ValueError(f"Score must be numeric, got {type(score)}")
        if not (0.0 <= score <= 1.0):
            raise ValueError(f"Score must be between 0 and 1, got {score}")
        return float(score)
