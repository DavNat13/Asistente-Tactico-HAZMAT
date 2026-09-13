from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)

def _uuid() -> str:
    return str(uuid4())


class Source(BaseModel):
    page: int = Field(..., ge=0)
    source: str = Field(default="GRE")
    score: float = Field(..., ge=0.0, le=1.0)
    text_snippet: Optional[str] = Field(default=None)


class Message(BaseModel):
    message_id: str = Field(default_factory=_uuid)
    role: str = Field(..., pattern=r"^(user|assistant)$")
    content: str = Field(..., min_length=1, max_length=50000)
    sources: list[Source] = Field(default_factory=list)
    context_used: int = Field(default=0, ge=0)
    timestamp: datetime = Field(default_factory=_utcnow)

    @field_validator("content")
    @classmethod
    def strip_content(cls, v: str) -> str:
        return v.strip()


class Thread(BaseModel):
    thread_id: str = Field(default_factory=_uuid)
    title: str = Field(default="Nueva consulta", max_length=200)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
    is_active: bool = True
    messages: list[Message] = Field(default_factory=list)

    def add_message(self, message: Message) -> None:
        self.messages.append(message)
        self.updated_at = _utcnow()

    def get_last_n_messages(self, n: int) -> list[Message]:
        return self.messages[-n:] if self.messages else []

    @property
    def message_count(self) -> int:
        return len(self.messages)

    @property
    def user_message_count(self) -> int:
        return sum(1 for m in self.messages if m.role == "user")


class Session(BaseModel):
    session_id: str = Field(default_factory=_uuid)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
    title: Optional[str] = Field(default=None, max_length=200)
    is_active: bool = True
    threads: list[Thread] = Field(default_factory=list)

    def create_thread(self, title: Optional[str] = None) -> Thread:
        thread = Thread(title=title or "Nueva consulta")
        self.threads.append(thread)
        self.updated_at = _utcnow()
        return thread

    def get_thread(self, thread_id: str) -> Optional[Thread]:
        for t in self.threads:
            if t.thread_id == thread_id and t.is_active:
                return t
        return None

    def get_active_threads(self) -> list[Thread]:
        return [t for t in self.threads if t.is_active]

    def get_or_create_thread(self, thread_id: Optional[str] = None) -> Thread:
        if thread_id:
            t = self.get_thread(thread_id)
            if t:
                return t
        return self.create_thread()

    @property
    def thread_count(self) -> int:
        return len([t for t in self.threads if t.is_active])

    @property
    def total_messages(self) -> int:
        return sum(t.message_count for t in self.threads if t.is_active)

    def soft_delete(self) -> None:
        self.is_active = False
        self.updated_at = _utcnow()
