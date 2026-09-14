import os
import sys

from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import (
    ConnectionFailure,
    OperationFailure,
    ServerSelectionTimeoutError,
)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import settings

from .message_repository import MessageRepository
from .models import Message, Session, Thread
from .session_crud import SessionCRUD
from .session_queries import SessionQueries
from .thread_repository import ThreadRepository


class SessionRepository:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if SessionRepository._initialized and hasattr(self, "client"):
            try:
                self.client.admin.command("ping")
                return
            except (ConnectionFailure, ServerSelectionTimeoutError):
                SessionRepository._initialized = False
        self.client: MongoClient = MongoClient(settings.MONGODB_URI)
        self.db: Database = self.client[settings.MONGODB_DB_NAME]
        self.collection: Collection = self.db[settings.SESSION_COLLECTION_NAME]
        self._crud = SessionCRUD(self.collection)
        self.threads = ThreadRepository(self.collection)
        self.messages = MessageRepository(self.collection)
        self._queries = SessionQueries(self.collection)
        self._ensure_indexes()
        SessionRepository._initialized = True

    def _ensure_indexes(self) -> None:
        try:
            self.collection.create_index(
                [("session_id", ASCENDING)],
                unique=True,
                name="idx_session_id_unique",
            )
            self.collection.create_index(
                [("is_active", DESCENDING), ("updated_at", DESCENDING)],
                name="idx_active_sessions_updated",
            )
            self.collection.create_index(
                [("threads.thread_id", ASCENDING)],
                name="idx_thread_id",
            )
            self.collection.create_index(
                [("updated_at", ASCENDING)],
                expireAfterSeconds=settings.SESSION_TTL_DAYS * 24 * 60 * 60,
                name="idx_ttl_cleanup",
            )
        except OperationFailure:
            pass

    def create_session(self, session: Session) -> Session:
        return self._crud.create_session(session)

    def get_session(self, session_id: str) -> Session | None:
        return self._crud.get_session(session_id)

    def update_session(self, session: Session) -> bool:
        return self._crud.update_session(session)

    def delete_session(self, session_id: str) -> bool:
        return self._crud.delete_session(session_id)

    def get_user_sessions(self, limit: int = 50, skip: int = 0) -> list[Session]:
        return self._queries.get_user_sessions(limit=limit, skip=skip)

    def get_session_stats(self, session_id: str) -> dict:
        return self._queries.get_session_stats(session_id)

    def add_thread(self, session_id: str, thread: Thread) -> bool:
        return self.threads.add_thread(session_id, thread)

    def get_thread(self, session_id: str, thread_id: str) -> Thread | None:
        return self.threads.get_thread(session_id, thread_id)

    def update_thread_title(self, session_id: str, thread_id: str, title: str) -> bool:
        return self.threads.update_thread_title(session_id, thread_id, title)

    def add_message(self, session_id: str, thread_id: str, message: Message) -> bool:
        return self.messages.add_message(session_id, thread_id, message)

    def get_messages(
        self, session_id: str, thread_id: str, limit: int = 100, skip: int = 0
    ) -> list[Message]:
        return self.messages.get_messages(session_id, thread_id, limit=limit, skip=skip)

    def close(self) -> None:
        if self.client:
            self.client.close()
