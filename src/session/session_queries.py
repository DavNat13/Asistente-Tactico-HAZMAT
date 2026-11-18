from pymongo import DESCENDING
from pymongo.errors import PyMongoError

from .models import Session
from .security import InputSanitizer


class SessionQueries:
    def __init__(self, collection):
        self.collection = collection

    def get_latest_for_user(self, user_id: str) -> Session | None:
        """Sesión activa más reciente del usuario (aislamiento entre usuarios)."""
        try:
            doc = self.collection.find_one(
                {"user_id": user_id, "is_active": True},
                sort=[("updated_at", DESCENDING)],
            )
            return (
                Session(**{k: v for k, v in doc.items() if k != "_id"}) if doc else None
            )
        except PyMongoError as e:
            raise RuntimeError(f"Failed to get user session: {e}")

    def delete_user_data(self, user_id: str) -> int:
        """Derecho de supresión: elimina físicamente las sesiones del usuario."""
        try:
            return self.collection.delete_many({"user_id": user_id}).deleted_count
        except PyMongoError as e:
            raise RuntimeError(f"Failed to delete user data: {e}")

    def get_user_sessions(
        self,
        user_id: str,
        limit: int = 50,
        skip: int = 0,
    ) -> list[Session]:
        try:
            cursor = (
                self.collection.find({"is_active": True, "user_id": user_id})
                .sort("updated_at", DESCENDING)
                .skip(skip)
                .limit(limit)
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
                {
                    "threads.thread_id": 1,
                    "threads.title": 1,
                    "threads.messages": 1,
                    "created_at": 1,
                    "updated_at": 1,
                },
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
                    {
                        "thread_id": t["thread_id"],
                        "title": t.get("title", "Untitled"),
                        "message_count": len(t.get("messages", [])),
                    }
                    for t in threads
                ],
            }
        except PyMongoError as e:
            raise RuntimeError(f"Failed to get stats: {e}")
