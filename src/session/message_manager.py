from .models import Message, Source
from .repository import SessionRepository
from .security import InputSanitizer


class MessageManager:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if MessageManager._initialized:
            return
        self.repo = SessionRepository()
        MessageManager._initialized = True

    def add_user_message(
        self, session_id: str, thread_id: str, content: str
    ) -> Message:
        content = InputSanitizer.sanitize_message_content(content)
        message = Message(role="user", content=content)
        self.repo.add_message(session_id, thread_id, message)
        self._maybe_update_title(session_id, thread_id, content)
        return message

    def add_assistant_message(
        self,
        session_id: str,
        thread_id: str,
        content: str,
        sources: list[dict] | None = None,
        context_used: int = 0,
    ) -> Message:
        content = InputSanitizer.sanitize_message_content(content)
        parsed = self._parse_sources(sources or [])
        message = Message(
            role="assistant",
            content=content,
            sources=parsed,
            context_used=context_used,
        )
        self.repo.add_message(session_id, thread_id, message)
        return message

    def get_history(
        self,
        session_id: str,
        thread_id: str,
        limit: int = 100,
        skip: int = 0,
    ) -> list[Message]:
        return self.repo.get_messages(session_id, thread_id, limit=limit, skip=skip)

    def get_history_for_llm(
        self,
        session_id: str,
        thread_id: str,
        max_messages: int = 6,
    ) -> list[dict]:
        messages = self.get_history(session_id, thread_id, limit=max_messages)
        return [{"role": m.role, "content": m.content} for m in messages]

    def _parse_sources(self, sources: list[dict]) -> list[Source]:
        parsed = []
        for s in sources:
            try:
                parsed.append(
                    Source(
                        page=s.get("page", 0),
                        source=s.get("source", "GRE"),
                        score=InputSanitizer.validate_score(s.get("score", 0.0)),
                        text_snippet=s.get("text_snippet"),
                    )
                )
            except (ValueError, KeyError):
                pass
        return parsed

    def _maybe_update_title(
        self, session_id: str, thread_id: str, content: str
    ) -> None:
        thread = self.repo.get_thread(session_id, thread_id)
        if not thread:
            return
        if thread.user_message_count == 1:
            title = content[:60].strip()
            if len(content) > 60:
                title += "..."
            self.repo.update_thread_title(session_id, thread_id, title)
