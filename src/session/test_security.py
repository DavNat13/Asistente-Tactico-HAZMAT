import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.session.security import InputSanitizer


class TestInputSanitizer:
    def test_sanitize_normal_string(self):
        result = InputSanitizer.sanitize_string("Hello world")
        assert result == "Hello world"

    def test_operator_keys_rejected(self):
        with pytest.raises(ValueError):
            InputSanitizer.sanitize_dict({"$ne": None})
        with pytest.raises(ValueError):
            InputSanitizer.sanitize_dict({"a": {"$where": "1"}})

    def test_text_values_are_stored_not_blocked(self):
        # El texto se guarda con consultas parametrizadas; el XSS se neutraliza al renderizar.
        text = "<script>alert('xss')</script> $in"
        assert InputSanitizer.sanitize_string(text) == text

    def test_control_chars_removed(self):
        assert InputSanitizer.sanitize_string("ok\x00\x07") == "ok"

    def test_username(self):
        assert InputSanitizer.sanitize_username(" Bombero.1 ") == "bombero.1"
        with pytest.raises(ValueError):
            InputSanitizer.sanitize_username("a$b")

    def test_sanitize_uuid_valid(self):
        result = InputSanitizer.sanitize_uuid("550e8400-e29b-41d4-a716-446655440000")
        assert result == "550e8400-e29b-41d4-a716-446655440000"

    def test_sanitize_uuid_invalid(self):
        with pytest.raises(ValueError):
            InputSanitizer.sanitize_uuid("not-a-uuid")

    def test_validate_role_valid(self):
        assert InputSanitizer.validate_role("user") == "user"
        assert InputSanitizer.validate_role("ASSISTANT") == "assistant"

    def test_validate_role_invalid(self):
        with pytest.raises(ValueError):
            InputSanitizer.validate_role("admin")

    def test_validate_score_valid(self):
        assert InputSanitizer.validate_score(0.5) == 0.5
        assert InputSanitizer.validate_score(0) == 0.0
        assert InputSanitizer.validate_score(1) == 1.0

    def test_validate_score_invalid(self):
        with pytest.raises(ValueError):
            InputSanitizer.validate_score(-0.1)
        with pytest.raises(ValueError):
            InputSanitizer.validate_score(1.1)
