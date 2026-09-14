from datetime import datetime, timezone

from pymongo.errors import PyMongoError

from .models import Thread
from .security import InputSanitizer


class ThreadRepository:
    def __init__(self, collection):
        self.collection = collection

    def add_thread(self, session_id: str, thread: Thread) -> bool:
        try:
            session_id = InputSanitizer.sanitize_uuid(session_id)
            thread_doc = thread.model_dump(mode="json")
            result = self.collection.update_one(
                {"session_id": session_id},
                {
                    "$push": {"threads": thread_doc},
                    "$set": {"updated_at": datetime.now(timezone.utc)},
                },
            )
            return result.modified_count > 0
        except PyMongoError as e:
            raise RuntimeError(f"Failed to add thread: {e}")

    def get_thread(self, session_id: str, thread_id: str) -> Thread | None:
        try:
            session_id = InputSanitizer.sanitize_uuid(session_id)
            thread_id = InputSanitizer.sanitize_uuid(thread_id)
            doc = self.collection.find_one(
                {
                    "session_id": session_id,
                    "threads.thread_id": thread_id,
                    "is_active": True,
                },
                {"threads.$": 1},
            )
            if doc and "threads" in doc and doc["threads"]:
                thread_doc = doc["threads"][0]
                thread_doc.pop("_id", None)
                return Thread(**thread_doc)
            return None
        except PyMongoError as e:
            raise RuntimeError(f"Failed to retrieve thread: {e}")

    def update_thread_title(self, session_id: str, thread_id: str, title: str) -> bool:
        try:
            session_id = InputSanitizer.sanitize_uuid(session_id)
            thread_id = InputSanitizer.sanitize_uuid(thread_id)
            title = InputSanitizer.sanitize_title(title)
            result = self.collection.update_one(
                {"session_id": session_id, "threads.thread_id": thread_id},
                {
                    "$set": {
                        "threads.$.title": title,
                        "threads.$.updated_at": datetime.now(timezone.utc),
                        "updated_at": datetime.now(timezone.utc),
                    }
                },
            )
            return result.modified_count > 0
        except PyMongoError as e:
            raise RuntimeError(f"Failed to update title: {e}")
