from io import BytesIO

from .export_manager import ExportManager
from .message_manager import MessageManager
from .models import Message, Session, Thread
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

    def create_session(self, user_id: str | None = None) -> Session:
        session = Session(user_id=user_id)
        session.create_thread(title="Nueva consulta")
        self.repo.create_session(session)
        return session

    def get_or_create_session(self, session_id: str | None = None) -> Session:
        if session_id:
            try:
                session_id = InputSanitizer.sanitize_uuid(session_id)
                session = self.repo.get_session(session_id)
                if session:
                    return session
            except (ValueError, RuntimeError):
                pass
        return self.create_session()

    def get_or_create_user_session(self, user_id: str) -> Session:
        """La sesión SIEMPRE se resuelve desde el usuario autenticado (nunca desde la URL)."""
        return self.repo.get_latest_for_user(user_id) or self.create_session(user_id)

    def delete_user_data(self, user_id: str) -> int:
        return self.repo.delete_user_data(user_id)

    def get_session(self, session_id: str) -> Session | None:
        return self.repo.get_session(session_id)

    def delete_session(self, session_id: str) -> bool:
        return self.repo.delete_session(session_id)

    def create_thread(self, session_id: str, title: str | None = None) -> Thread:
        session = self.repo.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        thread = session.create_thread(title=title)
        self.repo.add_thread(session_id, thread)
        return thread

    def get_thread(self, session_id: str, thread_id: str) -> Thread | None:
        return self.repo.get_thread(session_id, thread_id)

    def rename_thread(self, session_id: str, thread_id: str, title: str) -> bool:
        return self.repo.update_thread_title(session_id, thread_id, title)

    def set_incident(
        self, session_id: str, thread_id: str, incident: dict | None
    ) -> bool:
        return self.repo.set_incident(session_id, thread_id, incident)

    def delete_thread(self, session_id: str, thread_id: str) -> bool:
        return self.repo.delete_thread(session_id, thread_id)

    def get_active_threads(self, session_id: str) -> list[Thread]:
        session = self.repo.get_session(session_id)
        return session.get_active_threads() if session else []

    def switch_thread(self, session_id: str, thread_id: str) -> Thread | None:
        thread = self.repo.get_thread(session_id, thread_id)
        return thread if thread else self.create_thread(session_id)

    def get_or_create_thread(
        self, session_id: str, thread_id: str | None = None
    ) -> Thread:
        if thread_id:
            thread = self.repo.get_thread(session_id, thread_id)
            if thread:
                return thread
        return self.create_thread(session_id)

    def add_user_message(
        self, session_id: str, thread_id: str, content: str
    ) -> Message:
        return MessageManager().add_user_message(session_id, thread_id, content)

    def add_assistant_message(
        self,
        session_id: str,
        thread_id: str,
        content: str,
        sources: list[dict] | None = None,
        context_used: int = 0,
    ) -> Message:
        return MessageManager().add_assistant_message(
            session_id,
            thread_id,
            content,
            sources=sources,
            context_used=context_used,
        )

    def get_history(
        self, session_id: str, thread_id: str, limit: int = 100, skip: int = 0
    ) -> list[Message]:
        return MessageManager().get_history(
            session_id, thread_id, limit=limit, skip=skip
        )

    def export_chat_bytes(
        self, session_id: str, thread_id: str, fmt: str = "json"
    ) -> BytesIO | None:
        return ExportManager().export_bytes(session_id, thread_id, export_format=fmt)

    def get_session_stats(self, session_id: str) -> dict:
        return self.repo.get_session_stats(session_id)

    def list_sessions(self, user_id: str, limit: int = 50) -> list[Session]:
        return self.repo.get_user_sessions(user_id, limit=limit)

    def close(self) -> None:
        self.repo.close()
