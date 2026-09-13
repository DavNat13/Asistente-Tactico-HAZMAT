from typing import Optional
from io import BytesIO

from .models import Session, Thread, Message
from .repository import SessionRepository
from .security import InputSanitizer
from .message_manager import MessageManager
from .export_manager import ExportManager


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

    def get_or_create_session(self, session_id: Optional[str] = None) -> Session:
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

    def create_thread(self, session_id: str, title: Optional[str] = None) -> Thread:
        session = self.repo.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        thread = session.create_thread(title=title)
        self.repo.add_thread(session_id, thread)
        return thread

    def get_thread(self, session_id: str, thread_id: str) -> Optional[Thread]:
        return self.repo.get_thread(session_id, thread_id)

    def get_active_threads(self, session_id: str) -> list[Thread]:
        session = self.repo.get_session(session_id)
        return session.get_active_threads() if session else []

    def switch_thread(self, session_id: str, thread_id: str) -> Optional[Thread]:
        thread = self.repo.get_thread(session_id, thread_id)
        return thread if thread else self.create_thread(session_id)

    def get_or_create_thread(self, session_id: str, thread_id: Optional[str] = None) -> Thread:
        if thread_id:
            thread = self.repo.get_thread(session_id, thread_id)
            if thread:
                return thread
        return self.create_thread(session_id)

    def add_user_message(self, session_id: str, thread_id: str, content: str) -> Message:
        return MessageManager().add_user_message(session_id, thread_id, content)

    def add_assistant_message(
        self, session_id: str, thread_id: str, content: str,
        sources: Optional[list[dict]] = None, context_used: int = 0,
    ) -> Message:
        return MessageManager().add_assistant_message(
            session_id, thread_id, content, sources=sources, context_used=context_used,
        )

    def get_history(self, session_id: str, thread_id: str, limit: int = 100, skip: int = 0) -> list[Message]:
        return MessageManager().get_history(session_id, thread_id, limit=limit, skip=skip)

    def export_chat_bytes(self, session_id: str, thread_id: str, fmt: str = "json") -> Optional[BytesIO]:
        return ExportManager().export_bytes(session_id, thread_id, export_format=fmt)

    def get_session_stats(self, session_id: str) -> dict:
        return self.repo.get_session_stats(session_id)

    def list_sessions(self, limit: int = 50) -> list[Session]:
        return self.repo.get_user_sessions(limit=limit)

    def close(self) -> None:
        self.repo.close()
