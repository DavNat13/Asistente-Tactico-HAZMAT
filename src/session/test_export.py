import json
import pytest

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.session.models import Session, Thread, Message, Source


class TestExport:
    def test_export_json_structure(self):
        session = Session()
        thread = session.create_thread("Export Test")
        thread.add_message(Message(role="user", content="Test question"))
        thread.add_message(
            Message(
                role="assistant", content="Test answer",
                sources=[Source(page=1, source="GRE", score=0.9)],
            )
        )
        export_data = {
            "thread": {
                "thread_id": thread.thread_id,
                "title": thread.title,
                "message_count": thread.message_count,
            },
            "messages": [
                {"role": m.role, "content": m.content,
                 "timestamp": m.timestamp.isoformat()}
                for m in thread.messages
            ],
        }
        json_str = json.dumps(export_data, ensure_ascii=False)
        assert "Export Test" in json_str
        assert len(export_data["messages"]) == 2
