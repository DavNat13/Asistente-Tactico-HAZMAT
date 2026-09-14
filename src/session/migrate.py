import json

from src.session.manager import SessionManager


def migrate_in_memory_data(
    history: list[dict],
    session_id: str | None = None,
) -> str:
    manager = SessionManager()
    if session_id:
        session = manager.get_or_create_session(session_id)
    else:
        session = manager.create_session()
    thread = (
        session.threads[0]
        if session.threads
        else manager.create_thread(session.session_id)
    )
    migrated = 0
    for msg in history:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if not content:
            continue
        if role == "user":
            manager.add_user_message(
                session.session_id,
                thread.thread_id,
                content,
            )
        elif role == "assistant":
            manager.add_assistant_message(
                session.session_id,
                thread.thread_id,
                content,
                sources=msg.get("sources", []),
                context_used=msg.get("context_used", 0),
            )
        migrated += 1
    print(f"Migration complete: {migrated} messages migrated")
    print(f"Session ID: {session.session_id}")
    print(f"Thread ID: {thread.thread_id}")
    return session.session_id


def migrate_from_json_file(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    messages = data.get("messages", [])
    return migrate_in_memory_data(messages)
