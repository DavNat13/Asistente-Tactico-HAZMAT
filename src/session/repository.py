"""
MongoDB repository for HAZMAT chat sessions.

Handles all database operations with proper indexing,
error handling, and performance optimizations.
"""

from datetime import datetime, timezone
from typing import Optional

from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import (
    DuplicateKeyError,
    PyMongoError,
    OperationFailure,
)
from pymongo.collection import Collection
from pymongo.database import Database

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import settings
from .models import Session, Thread, Message, Source
from .security import InputSanitizer


class SessionRepository:
    """
    MongoDB repository for session persistence.

    Provides CRUD operations with automatic indexing,
    error handling, and input validation.
    """

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if SessionRepository._initialized:
            return

        self.client: MongoClient = MongoClient(settings.MONGODB_URI)
        self.db: Database = self.client[settings.MONGODB_DB_NAME]
        self.collection: Collection = self.db[settings.SESSION_COLLECTION_NAME]

        self._ensure_indexes()
        SessionRepository._initialized = True

    def _ensure_indexes(self) -> None:
        """Create indexes for optimal query performance."""
        try:
            # Unique index on session_id
            self.collection.create_index(
                [("session_id", ASCENDING)],
                unique=True,
                name="idx_session_id_unique",
            )

            # Index for listing active sessions by update time
            self.collection.create_index(
                [("is_active", DESCENDING), ("updated_at", DESCENDING)],
                name="idx_active_sessions_updated",
            )

            # Index for thread lookups within sessions
            self.collection.create_index(
                [("threads.thread_id", ASCENDING)],
                name="idx_thread_id",
            )

            # TTL index for automatic cleanup of old sessions (90 days)
            self.collection.create_index(
                [("updated_at", ASCENDING)],
                expireAfterSeconds=settings.SESSION_TTL_DAYS * 24 * 60 * 60,
                name="idx_ttl_cleanup",
            )

            print("[SessionRepository] Indexes verified successfully")
        except OperationFailure as e:
            print(f"[SessionRepository] Index creation warning: {e}")

    # ──────────────────────────────────────────────────────
    # Session CRUD
    # ──────────────────────────────────────────────────────

    def create_session(self, session: Session) -> Session:
        """Persist a new session to MongoDB."""
        try:
            # Sanitize input
            session.session_id = InputSanitizer.sanitize_uuid(
                session.session_id
            )

            doc = session.model_dump(mode="json")
            doc["_id"] = session.session_id  # Use session_id as _id

            self.collection.insert_one(doc)
            return session

        except DuplicateKeyError:
            raise ValueError(
                f"Session {session.session_id} already exists"
            )
        except PyMongoError as e:
            raise RuntimeError(f"Failed to create session: {e}")

    def get_session(self, session_id: str) -> Optional[Session]:
        """Retrieve a session by ID."""
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
        """Update an existing session."""
        try:
            session.updated_at = datetime.now(timezone.utc)
            doc = session.model_dump(mode="json")
            doc.pop("session_id", None)  # Don't update the ID field

            result = self.collection.update_one(
                {"session_id": session.session_id},
                {"$set": doc},
            )
            return result.modified_count > 0

        except PyMongoError as e:
            raise RuntimeError(f"Failed to update session: {e}")

    def delete_session(self, session_id: str) -> bool:
        """Soft-delete a session."""
        try:
            session_id = InputSanitizer.sanitize_uuid(session_id)
            result = self.collection.update_one(
                {"session_id": session_id},
                {
                    "$set": {
                        "is_active": False,
                        "updated_at": datetime.now(timezone.utc),
                    }
                },
            )
            return result.modified_count > 0

        except PyMongoError as e:
            raise RuntimeError(f"Failed to delete session: {e}")

    def hard_delete_session(self, session_id: str) -> bool:
        """Permanently remove a session (admin use only)."""
        try:
            session_id = InputSanitizer.sanitize_uuid(session_id)
            result = self.collection.delete_one(
                {"session_id": session_id}
            )
            return result.deleted_count > 0

        except PyMongoError as e:
            raise RuntimeError(f"Failed to hard delete session: {e}")

    # ──────────────────────────────────────────────────────
    # Thread Operations
    # ──────────────────────────────────────────────────────

    def add_thread(self, session_id: str, thread: Thread) -> bool:
        """Add a new thread to an existing session."""
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

    def get_thread(
        self, session_id: str, thread_id: str
    ) -> Optional[Thread]:
        """Retrieve a specific thread from a session."""
        try:
            session_id = InputSanitizer.sanitize_uuid(session_id)
            thread_id = InputSanitizer.sanitize_uuid(thread_id)

            doc = self.collection.find_one(
                {
                    "session_id": session_id,
                    "threads.thread_id": thread_id,
                    "is_active": True,
                },
                {
                    "threads.$": 1,
                },
            )

            if doc and "threads" in doc and doc["threads"]:
                thread_doc = doc["threads"][0]
                thread_doc.pop("_id", None)
                return Thread(**thread_doc)
            return None

        except PyMongoError as e:
            raise RuntimeError(f"Failed to retrieve thread: {e}")

    # ──────────────────────────────────────────────────────
    # Message Operations
    # ──────────────────────────────────────────────────────

    def add_message(
        self,
        session_id: str,
        thread_id: str,
        message: Message,
    ) -> bool:
        """Append a message to a thread."""
        try:
            session_id = InputSanitizer.sanitize_uuid(session_id)
            thread_id = InputSanitizer.sanitize_uuid(thread_id)

            message_doc = message.model_dump(mode="json")

            result = self.collection.update_one(
                {
                    "session_id": session_id,
                    "threads.thread_id": thread_id,
                },
                {
                    "$push": {"threads.$.messages": message_doc},
                    "$set": {"updated_at": datetime.now(timezone.utc)},
                },
            )
            return result.modified_count > 0

        except PyMongoError as e:
            raise RuntimeError(f"Failed to add message: {e}")

    def get_messages(
        self,
        session_id: str,
        thread_id: str,
        limit: int = 100,
        skip: int = 0,
    ) -> list[Message]:
        """Retrieve messages from a thread with pagination."""
        try:
            session_id = InputSanitizer.sanitize_uuid(session_id)
            thread_id = InputSanitizer.sanitize_uuid(thread_id)

            pipeline = [
                {"$match": {"session_id": session_id, "threads.thread_id": thread_id}},
                {"$unwind": "$threads"},
                {"$match": {"threads.thread_id": thread_id}},
                {"$project": {"messages": {"$slice": ["$threads.messages", skip, limit]}}},
            ]

            results = list(self.collection.aggregate(pipeline))

            if not results or not results[0].get("messages"):
                return []

            return [
                Message(**m) for m in results[0]["messages"]
            ]

        except PyMongoError as e:
            raise RuntimeError(f"Failed to retrieve messages: {e}")

    # ──────────────────────────────────────────────────────
    # Query Helpers
    # ──────────────────────────────────────────────────────

    def get_user_sessions(
        self,
        limit: int = 50,
        skip: int = 0,
    ) -> list[Session]:
        """List active sessions ordered by last update."""
        try:
            cursor = (
                self.collection.find({"is_active": True})
                .sort("updated_at", DESCENDING)
                .skip(skip)
                .limit(limit)
            )

            sessions = []
            for doc in cursor:
                doc.pop("_id", None)
                sessions.append(Session(**doc))

            return sessions

        except PyMongoError as e:
            raise RuntimeError(f"Failed to list sessions: {e}")

    def get_session_stats(self, session_id: str) -> dict:
        """Get statistics for a session."""
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
            total_messages = sum(
                len(t.get("messages", [])) for t in threads
            )

            return {
                "session_id": session_id,
                "created_at": doc.get("created_at"),
                "updated_at": doc.get("updated_at"),
                "thread_count": len(threads),
                "total_messages": total_messages,
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
            raise RuntimeError(f"Failed to get session stats: {e}")

    def update_thread_title(
        self,
        session_id: str,
        thread_id: str,
        title: str,
    ) -> bool:
        """Update a thread's title."""
        try:
            session_id = InputSanitizer.sanitize_uuid(session_id)
            thread_id = InputSanitizer.sanitize_uuid(thread_id)
            title = InputSanitizer.sanitize_title(title)

            result = self.collection.update_one(
                {
                    "session_id": session_id,
                    "threads.thread_id": thread_id,
                },
                {
                    "$set": {
                        "threads.$.title": title,
                        "threads.$.updated_at": datetime.now(timezone.utc),
                        "updated_at": datetime.now(timezone.utc),
                    },
                },
            )
            return result.modified_count > 0

        except PyMongoError as e:
            raise RuntimeError(f"Failed to update thread title: {e}")

    def close(self) -> None:
        """Close the MongoDB connection."""
        if self.client:
            self.client.close()
            print("[SessionRepository] Connection closed")
