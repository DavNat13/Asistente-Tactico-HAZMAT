"""
Tests for the HAZMAT session management system.

Run with: python -m pytest src/session/tests.py -v
"""

import json
import pytest
from datetime import datetime, timezone

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.session.models import Session, Thread, Message, Source
from src.session.security import InputSanitizer


class TestSource:
    """Tests for Source model."""

    def test_create_source(self):
        source = Source(page=1, source="GRE", score=0.85)
        assert source.page == 1
        assert source.source == "GRE"
        assert source.score == 0.85

    def test_source_score_boundary(self):
        # Valid scores
        Source(page=1, source="GRE", score=0.0)
        Source(page=1, source="GRE", score=1.0)

        # Invalid scores
        with pytest.raises(Exception):
            Source(page=1, source="GRE", score=-0.1)
        with pytest.raises(Exception):
            Source(page=1, source="GRE", score=1.1)


class TestMessage:
    """Tests for Message model."""

    def test_create_user_message(self):
        msg = Message(role="user", content="Test query")
        assert msg.role == "user"
        assert msg.content == "Test query"
        assert msg.message_id  # Auto-generated UUID
        assert msg.timestamp

    def test_create_assistant_message(self):
        sources = [Source(page=1, source="GRE", score=0.9)]
        msg = Message(
            role="assistant",
            content="Here is the answer",
            sources=sources,
            context_used=5,
        )
        assert msg.role == "assistant"
        assert len(msg.sources) == 1
        assert msg.context_used == 5

    def test_invalid_role(self):
        with pytest.raises(Exception):
            Message(role="admin", content="Test")

    def test_empty_content(self):
        with pytest.raises(Exception):
            Message(role="user", content="")

    def test_content_stripped(self):
        msg = Message(role="user", content="  test  ")
        assert msg.content == "test"


class TestThread:
    """Tests for Thread model."""

    def test_create_thread(self):
        thread = Thread()
        assert thread.thread_id
        assert thread.title == "Nueva consulta"
        assert thread.is_active is True
        assert thread.messages == []

    def test_add_message(self):
        thread = Thread()
        msg = Message(role="user", content="Hello")
        thread.add_message(msg)
        assert thread.message_count == 1
        assert thread.user_message_count == 1

    def test_get_last_n_messages(self):
        thread = Thread()
        for i in range(10):
            thread.add_message(
                Message(role="user", content=f"Message {i}")
            )
        last_3 = thread.get_last_n_messages(3)
        assert len(last_3) == 3
        assert last_3[0].content == "Message 7"


class TestSession:
    """Tests for Session model."""

    def test_create_session(self):
        session = Session()
        assert session.session_id
        assert session.is_active is True
        assert session.threads == []

    def test_create_thread(self):
        session = Session()
        thread = session.create_thread("Test Thread")
        assert thread.title == "Test Thread"
        assert len(session.threads) == 1
        assert session.thread_count == 1

    def test_get_thread(self):
        session = Session()
        thread = session.create_thread()
        found = session.get_thread(thread.thread_id)
        assert found is not None
        assert found.thread_id == thread.thread_id

    def test_get_nonexistent_thread(self):
        session = Session()
        found = session.get_thread("nonexistent-id")
        assert found is None

    def test_soft_delete(self):
        session = Session()
        session.soft_delete()
        assert session.is_active is False

    def test_total_messages(self):
        session = Session()
        t1 = session.create_thread()
        t2 = session.create_thread()
        t1.add_message(Message(role="user", content="Q1"))
        t1.add_message(Message(role="assistant", content="A1"))
        t2.add_message(Message(role="user", content="Q2"))
        assert session.total_messages == 3


class TestInputSanitizer:
    """Tests for security sanitization."""

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


class TestExport:
    """Tests for export functionality."""

    def test_export_json_structure(self):
        session = Session()
        thread = session.create_thread("Export Test")
        thread.add_message(
            Message(role="user", content="Test question")
        )
        thread.add_message(
            Message(
                role="assistant",
                content="Test answer",
                sources=[Source(page=1, source="GRE", score=0.9)],
            )
        )

        # Simulate export
        export_data = {
            "thread": {
                "thread_id": thread.thread_id,
                "title": thread.title,
                "message_count": thread.message_count,
            },
            "messages": [
                {
                    "role": m.role,
                    "content": m.content,
                    "timestamp": m.timestamp.isoformat(),
                }
                for m in thread.messages
            ],
        }

        json_str = json.dumps(export_data, ensure_ascii=False)
        assert "Export Test" in json_str
        assert len(export_data["messages"]) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
