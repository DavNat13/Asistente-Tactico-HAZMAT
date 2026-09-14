from datetime import datetime, timezone
from typing import Optional

from pymongo.errors import PyMongoError

from .models import Message
from .security import InputSanitizer


class MessageRepository:
    def __init__(self, collection):
        self.collection = collection

    def add_message(
        self, session_id: str, thread_id: str, message: Message
    ) -> bool:
        try:
            session_id = InputSanitizer.sanitize_uuid(session_id)
            thread_id = InputSanitizer.sanitize_uuid(thread_id)
            message_doc = message.model_dump(mode="json")
            result = self.collection.update_one(
                {"session_id": session_id,
                 "threads.thread_id": thread_id},
                {"$push": {"threads.$.messages": message_doc},
                 "$set": {"updated_at": datetime.now(timezone.utc)}},
            )
            return result.modified_count > 0
        except PyMongoError as e:
            raise RuntimeError(f"Failed to add message: {e}")

    def get_messages(
        self, session_id: str, thread_id: str,
        limit: int = 100, skip: int = 0,
    ) -> list[Message]:
        try:
            session_id = InputSanitizer.sanitize_uuid(session_id)
            thread_id = InputSanitizer.sanitize_uuid(thread_id)
            pipeline = [
                {"$match": {"session_id": session_id,
                            "threads.thread_id": thread_id}},
                {"$unwind": "$threads"},
                {"$match": {"threads.thread_id": thread_id}},
                {"$project": {
                    "messages": {"$slice": ["$threads.messages", skip, limit]}
                }},
            ]
            results = list(self.collection.aggregate(pipeline))
            if not results or not results[0].get("messages"):
                return []
            return [Message(**m) for m in results[0]["messages"]]
        except PyMongoError as e:
            raise RuntimeError(f"Failed to retrieve messages: {e}")
