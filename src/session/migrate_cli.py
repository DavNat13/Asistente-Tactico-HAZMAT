import argparse
import json

from .migrate import migrate_in_memory_data


def main():
    parser = argparse.ArgumentParser(description="Migrate HAZMAT chat data to MongoDB")
    parser.add_argument("--file", type=str, help="JSON file to migrate")
    parser.add_argument("--session-id", type=str, help="Existing session ID")
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview without writing"
    )
    args = parser.parse_args()

    if not args.file:
        print("No file specified. Use --file <path>.")
        return

    print(f"Migrating from file: {args.file}")
    with open(args.file, "r", encoding="utf-8") as f:
        data = json.load(f)
    messages = data.get("messages", [])
    print(f"Found {len(messages)} messages to migrate")

    if args.dry_run:
        for i, msg in enumerate(messages, 1):
            role = msg.get("role", "user")
            content = msg.get("content", "")
            preview = content[:80] + "..." if len(content) > 80 else content
            print(f"  [{i}] {role}: {preview}")
        print("Dry run complete. No changes made.")
    else:
        session_id = migrate_in_memory_data(messages)
        print(f"Successfully migrated to session: {session_id}")


if __name__ == "__main__":
    main()
