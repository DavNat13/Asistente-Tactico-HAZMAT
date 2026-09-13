import pytest

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.session.security import InputSanitizer


class TestInputSanitizer:
    def test_sanitize_normal_string(self):
        result = InputSanitizer.sanitize_string("Hello world")
        assert result == "Hello world"

    def test_sanitize_noSQL_injection(self):
        with pytest.raises(ValueError):
            InputSanitizer.sanitize_string('{"$ne": null}')

    def test_sanitize_xss(self):
        with pytest.raises(ValueError):
            InputSanitizer.sanitize_string("<script>alert('xss')</script>")

    def test_sanitize_uuid_valid(self):
        result = InputSanitizer.sanitize_uuid(
            "550e8400-e29b-41d4-a716-446655440000"
        )
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
