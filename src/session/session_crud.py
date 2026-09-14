from datetime import datetime, timezone
from typing import Optional

from pymongo.errors import DuplicateKeyError, PyMongoError

from .models import Session
from .security import InputSanitizer


class SessionCRUD:
    def __init__(self, collection):
        self.collection = collection

    def create_session(self, session: Session) -> Session:
        try:
            session.session_id = InputSanitizer.sanitize_uuid(
                session.session_id
            )
            doc = session.model_dump(mode="json")
            doc["_id"] = session.session_id
            self.collection.insert_one(doc)
            return session
        except DuplicateKeyError:
            raise ValueError(f"Session {session.session_id} exists")
        except PyMongoError as e:
            raise RuntimeError(f"Failed to create session: {e}")

    def get_session(self, session_id: str) -> Optional[Session]:
        try:
            session_id = InputSanitizer.sanitize_uuid(session_id)
            doc = self.collection.find_one(
                {"session_id": session_id, "is_active": True}
            )
            if doc:
                doc.pop("_id", None)
                return Session(**doc)
            return None
        except PyMongoError as e:
            raise RuntimeError(f"Failed to retrieve session: {e}")

    def update_session(self, session: Session) -> bool:
        try:
            session.updated_at = datetime.now(timezone.utc)
            doc = session.model_dump(mode="json")
            doc.pop("session_id", None)
            result = self.collection.update_one(
                {"session_id": session.session_id}, {"$set": doc}
            )
            return result.modified_count > 0
        except PyMongoError as e:
            raise RuntimeError(f"Failed to update session: {e}")

    def delete_session(self, session_id: str) -> bool:
        try:
            session_id = InputSanitizer.sanitize_uuid(session_id)
            result = self.collection.update_one(
                {"session_id": session_id},
                {"$set": {"is_active": False,
                           "updated_at": datetime.now(timezone.utc)}},
            )
            return result.modified_count > 0
        except PyMongoError as e:
            raise RuntimeError(f"Failed to delete session: {e}")
