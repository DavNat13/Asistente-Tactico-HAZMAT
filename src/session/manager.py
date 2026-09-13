"""
High-level session manager for HAZMAT chatbot.

Orchestrates session lifecycle, thread management,
message persistence, and chat export functionality.
"""

import json
from datetime import datetime, timezone
from io import BytesIO
from typing import Optional

from .models import Session, Thread, Message, Source
from .repository import SessionRepository
from .security import InputSanitizer


class SessionManager:
    """
    Manages the full lifecycle of chat sessions.

    Provides a clean API for:
    - Session creation and retrieval
    - Thread management (create, switch, list)
    - Message persistence with metadata
    - Chat export in JSON and Markdown formats
    """

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

    # ──────────────────────────────────────────────────────
    # Session Lifecycle
    # ──────────────────────────────────────────────────────

    def create_session(self) -> Session:
        """Create a new session with an initial thread."""
        session = Session()
        session.create_thread(title="Nueva consulta")

        self.repo.create_session(session)
        print(f"[SessionManager] Created session: {session.session_id}")
        return session

    def get_or_create_session(
        self, session_id: Optional[str] = None
    ) -> Session:
        """Retrieve an existing session or create a new one."""
        if session_id:
            try:
                session_id = InputSanitizer.sanitize_uuid(session_id)
                session = self.repo.get_session(session_id)
                if session:
                    return session
            except (ValueError, RuntimeError) as e:
                print(f"[SessionManager] Error retrieving session: {e}")

        return self.create_session()

    def get_session(self, session_id: str) -> Optional[Session]:
        """Retrieve a session by ID."""
        return self.repo.get_session(session_id)

    def delete_session(self, session_id: str) -> bool:
        """Soft-delete a session."""
        return self.repo.delete_session(session_id)

    # ──────────────────────────────────────────────────────
    # Thread Management
    # ──────────────────────────────────────────────────────

    def create_thread(
        self, session_id: str, title: Optional[str] = None
    ) -> Thread:
        """Create a new thread in a session."""
        session = self.repo.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        thread = session.create_thread(title=title)
        self.repo.add_thread(session_id, thread)

        print(
            f"[SessionManager] Created thread {thread.thread_id} "
            f"in session {session_id}"
        )
        return thread

    def get_thread(
        self, session_id: str, thread_id: str
    ) -> Optional[Thread]:
        """Retrieve a specific thread."""
        return self.repo.get_thread(session_id, thread_id)

    def get_active_threads(self, session_id: str) -> list[Thread]:
        """Get all active threads in a session."""
        session = self.repo.get_session(session_id)
        if not session:
            return []
        return session.get_active_threads()

    def switch_thread(
        self, session_id: str, thread_id: str
    ) -> Optional[Thread]:
        """Switch to an existing thread or create new."""
        thread = self.repo.get_thread(session_id, thread_id)
        if thread:
            return thread

        return self.create_thread(session_id)

    def get_or_create_thread(
        self, session_id: str, thread_id: Optional[str] = None
    ) -> Thread:
        """Get existing thread or create new one."""
        if thread_id:
            thread = self.repo.get_thread(session_id, thread_id)
            if thread:
                return thread

        return self.create_thread(session_id)

    # ──────────────────────────────────────────────────────
    # Message Operations
    # ──────────────────────────────────────────────────────

    def add_user_message(
        self,
        session_id: str,
        thread_id: str,
        content: str,
    ) -> Message:
        """Add a user message to a thread."""
        content = InputSanitizer.sanitize_message_content(content)

        message = Message(role="user", content=content)

        self.repo.add_message(session_id, thread_id, message)

        # Auto-generate thread title from first user message
        self._maybe_update_thread_title(
            session_id, thread_id, content
        )

        print(
            f"[SessionManager] Added user message to thread "
            f"{thread_id}"
        )
        return message

    def add_assistant_message(
        self,
        session_id: str,
        thread_id: str,
        content: str,
        sources: Optional[list[dict]] = None,
        context_used: int = 0,
    ) -> Message:
        """Add an assistant response to a thread."""
        content = InputSanitizer.sanitize_message_content(content)

        parsed_sources = []
        if sources:
            for s in sources:
                try:
                    parsed_sources.append(
                        Source(
                            page=s.get("page", 0),
                            source=s.get("source", "GRE"),
                            score=InputSanitizer.validate_score(
                                s.get("score", 0.0)
                            ),
                            text_snippet=s.get("text_snippet"),
                        )
                    )
                except (ValueError, KeyError) as e:
                    print(
                        f"[SessionManager] Skipping invalid source: {e}"
                    )

        message = Message(
            role="assistant",
            content=content,
            sources=parsed_sources,
            context_used=context_used,
        )

        self.repo.add_message(session_id, thread_id, message)

        print(
            f"[SessionManager] Added assistant message to thread "
            f"{thread_id}"
        )
        return message

    def get_history(
        self,
        session_id: str,
        thread_id: str,
        limit: int = 100,
        skip: int = 0,
    ) -> list[Message]:
        """Retrieve chat history for a thread."""
        return self.repo.get_messages(
            session_id, thread_id, limit=limit, skip=skip
        )

    def get_history_for_llm(
        self,
        session_id: str,
        thread_id: str,
        max_messages: int = 6,
    ) -> list[dict]:
        """
        Get recent history formatted for LLM context.

        Returns only the last N messages in the format
        expected by the generator.
        """
        messages = self.get_history(
            session_id, thread_id, limit=max_messages
        )
        return [
            {"role": m.role, "content": m.content}
            for m in messages
        ]

    # ──────────────────────────────────────────────────────
    # Chat Export
    # ──────────────────────────────────────────────────────

    def export_chat_json(
        self, session_id: str, thread_id: str
    ) -> Optional[str]:
        """Export a thread's chat history as JSON."""
        thread = self.repo.get_thread(session_id, thread_id)
        if not thread:
            return None

        export_data = {
            "export_info": {
                "format": "hazmat_chat_export",
                "version": "1.0",
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "session_id": session_id,
            },
            "thread": {
                "thread_id": thread.thread_id,
                "title": thread.title,
                "created_at": thread.created_at.isoformat(),
                "message_count": thread.message_count,
            },
            "messages": [
                {
                    "role": m.role,
                    "content": m.content,
                    "timestamp": m.timestamp.isoformat(),
                    "sources": [
                        {
                            "page": s.page,
                            "source": s.source,
                            "score": s.score,
                        }
                        for s in m.sources
                    ],
                    "context_used": m.context_used,
                }
                for m in thread.messages
            ],
        }

        return json.dumps(export_data, ensure_ascii=False, indent=2)

    def export_chat_markdown(
        self, session_id: str, thread_id: str
    ) -> Optional[str]:
        """Export a thread's chat history as Markdown."""
        thread = self.repo.get_thread(session_id, thread_id)
        if not thread:
            return None

        lines = [
            f"# HAZMAT Chat Export",
            f"",
            f"**Session:** `{session_id[:8]}...`",
            f"**Thread:** {thread.title}",
            f"**Date:** {thread.created_at.strftime('%Y-%m-%d %H:%M')}",
            f"**Messages:** {thread.message_count}",
            f"",
            f"---",
            f"",
        ]

        for msg in thread.messages:
            if msg.role == "user":
                lines.append(f"### 🧑 Usuario")
                lines.append(f"")
                lines.append(f"{msg.content}")
                lines.append(f"")
            else:
                lines.append(f"### 🤖 Asistente")
                lines.append(f"")
                lines.append(f"{msg.content}")
                lines.append(f"")

                if msg.sources:
                    lines.append(f"**Fuentes:**")
                    for src in msg.sources:
                        lines.append(
                            f"- Página {src.page} "
                            f"({src.source}) "
                            f"- Score: {src.score:.2f}"
                        )
                    lines.append(f"")

            lines.append(f"---")
            lines.append(f"")

        return "\n".join(lines)

    def export_chat_bytes(
        self,
        session_id: str,
        thread_id: str,
        format: str = "json",
    ) -> Optional[BytesIO]:
        """
        Export chat as downloadable bytes.

        Args:
            format: 'json' or 'markdown'

        Returns:
            BytesIO object ready for Streamlit download
        """
        if format == "json":
            content = self.export_chat_json(session_id, thread_id)
            mime = "application/json"
            ext = "json"
        elif format == "markdown":
            content = self.export_chat_markdown(session_id, thread_id)
            mime = "text/markdown"
            ext = "md"
        else:
            raise ValueError(f"Unsupported format: {format}")

        if not content:
            return None

        buffer = BytesIO(content.encode("utf-8"))
        buffer.name = f"hazmat_chat_{thread_id[:8]}.{ext}"
        return buffer

    # ──────────────────────────────────────────────────────
    # Statistics
    # ──────────────────────────────────────────────────────

    def get_session_stats(self, session_id: str) -> dict:
        """Get statistics for a session."""
        return self.repo.get_session_stats(session_id)

    def list_sessions(self, limit: int = 50) -> list[Session]:
        """List active sessions."""
        return self.repo.get_user_sessions(limit=limit)

    # ──────────────────────────────────────────────────────
    # Internal Helpers
    # ──────────────────────────────────────────────────────

    def _maybe_update_thread_title(
        self,
        session_id: str,
        thread_id: str,
        first_message: str,
    ) -> None:
        """Auto-generate thread title from first user message."""
        thread = self.repo.get_thread(session_id, thread_id)
        if not thread:
            return

        # Only update if this is the first user message
        if thread.user_message_count == 1:
            # Use first 60 chars as title
            title = first_message[:60].strip()
            if len(first_message) > 60:
                title += "..."

            self.repo.update_thread_title(
                session_id, thread_id, title
            )

    def close(self) -> None:
        """Clean up resources."""
        self.repo.close()
