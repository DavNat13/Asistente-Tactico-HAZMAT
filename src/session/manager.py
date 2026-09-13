from datetime import datetime, timezone
from typing import Optional

from .models import Session, Thread, Message, Source
from .repository import SessionRepository
from .security import InputSanitizer


class SessionManager:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if SessionManager._initialized:
            return
        self.repo = SessionRepository()
        SessionManager._initialized = True

    def create_session(self) -> Session:
        session = Session()
        session.create_thread(title="Nueva consulta")
        self.repo.create_session(session)
        return session

    def get_or_create_session(
        self, session_id: Optional[str] = None
    ) -> Session:
        if session_id:
            try:
                session_id = InputSanitizer.sanitize_uuid(session_id)
                session = self.repo.get_session(session_id)
                if session:
                    return session
            except (ValueError, RuntimeError):
                pass
        return self.create_session()

    def get_session(self, session_id: str) -> Optional[Session]:
        return self.repo.get_session(session_id)

    def delete_session(self, session_id: str) -> bool:
        return self.repo.delete_session(session_id)

    def create_thread(
        self, session_id: str, title: Optional[str] = None
    ) -> Thread:
        session = self.repo.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        thread = session.create_thread(title=title)
        self.repo.add_thread(session_id, thread)
        return thread

    def get_thread(
        self, session_id: str, thread_id: str
    ) -> Optional[Thread]:
        return self.repo.get_thread(session_id, thread_id)

    def get_active_threads(self, session_id: str) -> list[Thread]:
        session = self.repo.get_session(session_id)
        if not session:
            return []
        return session.get_active_threads()

    def switch_thread(
        self, session_id: str, thread_id: str
    ) -> Optional[Thread]:
        thread = self.repo.get_thread(session_id, thread_id)
        if thread:
            return thread
        return self.create_thread(session_id)

    def get_or_create_thread(
        self, session_id: str, thread_id: Optional[str] = None
    ) -> Thread:
        if thread_id:
            thread = self.repo.get_thread(session_id, thread_id)
            if thread:
                return thread
        return self.create_thread(session_id)

    def get_session_stats(self, session_id: str) -> dict:
        return self.repo.get_session_stats(session_id)

    def list_sessions(self, limit: int = 50) -> list[Session]:
        return self.repo.get_user_sessions(limit=limit)

    def close(self) -> None:
        self.repo.close()
