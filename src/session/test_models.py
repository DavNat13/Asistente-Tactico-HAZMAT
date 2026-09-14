import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.session.models import Session, Thread, Message, Source


class TestSource:
    def test_create_source(self):
        s = Source(page=1, source="GRE", score=0.85)
        assert s.page == 1 and s.score == 0.85

    def test_source_score_boundary(self):
        Source(page=1, source="GRE", score=0.0)
        Source(page=1, source="GRE", score=1.0)
        with pytest.raises(Exception):
            Source(page=1, source="GRE", score=-0.1)
        with pytest.raises(Exception):
            Source(page=1, source="GRE", score=1.1)


class TestMessage:
    def test_create_user_message(self):
        msg = Message(role="user", content="Test query")
        assert msg.role == "user" and msg.message_id

    def test_create_assistant_message(self):
        msg = Message(role="assistant", content="Answer",
                      sources=[Source(page=1, source="GRE", score=0.9)])
        assert len(msg.sources) == 1

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
    def test_create_thread(self):
        t = Thread()
        assert t.title == "Nueva consulta" and t.is_active

    def test_add_message(self):
        t = Thread()
        t.add_message(Message(role="user", content="Hello"))
        assert t.message_count == 1

    def test_get_last_n_messages(self):
        t = Thread()
        for i in range(10):
            t.add_message(Message(role="user", content=f"Msg {i}"))
        assert len(t.get_last_n_messages(3)) == 3


class TestSession:
    def test_create_session(self):
        s = Session()
        assert s.session_id and s.is_active

    def test_create_thread(self):
        s = Session()
        t = s.create_thread("Test")
        assert t.title == "Test" and len(s.threads) == 1

    def test_get_thread(self):
        s = Session()
        t = s.create_thread()
        assert s.get_thread(t.thread_id) is not None

    def test_get_nonexistent_thread(self):
        assert Session().get_thread("nope") is None

    def test_soft_delete(self):
        s = Session()
        s.soft_delete()
        assert not s.is_active

    def test_total_messages(self):
        s = Session()
        t1, t2 = s.create_thread(), s.create_thread()
        t1.add_message(Message(role="user", content="Q1"))
        t1.add_message(Message(role="assistant", content="A1"))
        t2.add_message(Message(role="user", content="Q2"))
        assert s.total_messages == 3
