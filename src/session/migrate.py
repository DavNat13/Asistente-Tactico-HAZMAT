"""
Migration script for converting in-memory session data to MongoDB.

Run this script to migrate any existing session_state data
to persistent MongoDB storage.

Usage:
    python -m src.session.migrate
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.session.manager import SessionManager
from src.session.models import Session, Thread, Message, Source


def migrate_in_memory_data(
    history: list[dict],
    session_id: str = None,
) -> str:
    """
    Migrate an in-memory history list to MongoDB.

    Args:
        history: List of message dicts with 'role', 'content', 'sources'
        session_id: Optional existing session ID to migrate into

    Returns:
        The session_id where data was migrated
    """
    manager = SessionManager()

    # Create or get session
    if session_id:
        session = manager.get_or_create_session(session_id)
    else:
        session = manager.create_session()

    # Get the default thread
    thread = session.threads[0] if session.threads else manager.create_thread(
        session.session_id
    )

    # Migrate each message
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
    """
    Migrate session data from a JSON export file.

    Args:
        file_path: Path to the JSON export file

    Returns:
        The session_id where data was migrated
    """
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    messages = data.get("messages", [])
    return migrate_in_memory_data(messages)


def main():
    """CLI entry point for migration."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Migrate HAZMAT chat data to MongoDB"
    )
    parser.add_argument(
        "--file",
        type=str,
        help="JSON file to migrate from",
    )
    parser.add_argument(
        "--session-id",
        type=str,
        help="Existing session ID to migrate into",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview migration without writing",
    )

    args = parser.parse_args()

    if args.file:
        print(f"Migrating from file: {args.file}")
        session_id = migrate_from_json_file(args.file)
        print(f"Successfully migrated to session: {session_id}")
    else:
        print("No file specified. Use --file <path> to migrate from JSON.")


if __name__ == "__main__":
    main()
