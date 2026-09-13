from typing import Optional

from pymongo import DESCENDING
from pymongo.errors import PyMongoError

from .models import Session
from .security import InputSanitizer


class SessionQueries:
    def __init__(self, collection):
        self.collection = collection

    def get_user_sessions(
        self, limit: int = 50, skip: int = 0,
    ) -> list[Session]:
        try:
            cursor = (
                self.collection.find({"is_active": True})
                .sort("updated_at", DESCENDING)
                .skip(skip).limit(limit)
            )
            return [
                Session(**{k: v for k, v in doc.items() if k != "_id"})
                for doc in cursor
            ]
        except PyMongoError as e:
            raise RuntimeError(f"Failed to list sessions: {e}")

    def get_session_stats(self, session_id: str) -> dict:
        try:
            session_id = InputSanitizer.sanitize_uuid(session_id)
            doc = self.collection.find_one(
                {"session_id": session_id},
                {"threads.thread_id": 1, "threads.title": 1,
                 "threads.messages": 1, "created_at": 1, "updated_at": 1},
            )
            if not doc:
                return {}
            threads = doc.get("threads", [])
            total = sum(len(t.get("messages", [])) for t in threads)
            return {
                "session_id": session_id,
                "created_at": doc.get("created_at"),
                "updated_at": doc.get("updated_at"),
                "thread_count": len(threads),
                "total_messages": total,
                "threads": [
                    {"thread_id": t["thread_id"],
                     "title": t.get("title", "Untitled"),
                     "message_count": len(t.get("messages", []))}
                    for t in threads
                ],
            }
        except PyMongoError as e:
            raise RuntimeError(f"Failed to get stats: {e}")
