import json
from datetime import datetime, timezone
from io import BytesIO

from .repository import SessionRepository


class ExportManager:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if ExportManager._initialized:
            return
        self.repo = SessionRepository()
        ExportManager._initialized = True

    def export_json(self, session_id: str, thread_id: str) -> str | None:
        thread = self.repo.get_thread(session_id, thread_id)
        if not thread:
            return None
        data = {
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
                        {"page": s.page, "source": s.source, "score": s.score}
                        for s in m.sources
                    ],
                    "context_used": m.context_used,
                }
                for m in thread.messages
            ],
        }
        return json.dumps(data, ensure_ascii=False, indent=2)

    def export_markdown(self, session_id: str, thread_id: str) -> str | None:
        thread = self.repo.get_thread(session_id, thread_id)
        if not thread:
            return None
        lines = [
            "# HAZMAT Chat Export",
            "",
            f"**Session:** `{session_id[:8]}...`",
            f"**Thread:** {thread.title}",
            f"**Date:** {thread.created_at.strftime('%Y-%m-%d %H:%M')}",
            f"**Messages:** {thread.message_count}",
            "",
            "---",
            "",
        ]
        for msg in thread.messages:
            if msg.role == "user":
                lines.extend(["### Usuario", "", msg.content, ""])
            else:
                lines.extend(["### Asistente", "", msg.content, ""])
                if msg.sources:
                    lines.append("**Fuentes:**")
                    for src in msg.sources:
                        lines.append(
                            f"- Pagina {src.page} ({src.source}) Score: {src.score:.2f}"
                        )
                    lines.append("")
            lines.extend(["---", ""])
        return "\n".join(lines)

    def export_bytes(
        self, session_id: str, thread_id: str, export_format: str = "json"
    ) -> BytesIO | None:
        if export_format == "json":
            content = self.export_json(session_id, thread_id)
            ext = "json"
        elif export_format == "markdown":
            content = self.export_markdown(session_id, thread_id)
            ext = "md"
        else:
            raise ValueError(f"Unsupported format: {export_format}")
        if not content:
            return None
        buf = BytesIO(content.encode("utf-8"))
        buf.name = f"hazmat_chat_{thread_id[:8]}.{ext}"
        return buf
