"""Exercise backup, deletion and restore in an explicitly selected laboratory database."""

import argparse
import os
from pathlib import Path
import subprocess
import sys
import uuid

from sqlalchemy import create_engine, text


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-laboratory-restore", action="store_true", required=True)
    parser.add_argument("backup", type=Path)
    args = parser.parse_args()
    engine = create_engine(os.environ["DATABASE_URL"])
    marker = "restore-check-" + uuid.uuid4().hex
    with engine.begin() as db:
        db.execute(text("INSERT INTO authors (name) VALUES (:name)"), {"name": marker})
    engine.dispose()
    subprocess.run([sys.executable, "scripts/database.py", "backup", str(args.backup)], check=True)
    with engine.begin() as db:
        before = db.scalar(text("SELECT count(*) FROM authors WHERE name=:name"), {"name": marker})
        db.execute(text("DELETE FROM authors WHERE name=:name"), {"name": marker})
    with engine.connect() as db:
        deleted = db.scalar(text("SELECT count(*) FROM authors WHERE name=:name"), {"name": marker})
    engine.dispose()
    subprocess.run([sys.executable, "scripts/database.py", "restore", str(args.backup)], check=True)
    with engine.connect() as db:
        restored = db.scalar(text("SELECT count(*) FROM authors WHERE name=:name"), {"name": marker})
    engine.dispose()
    print(f"Before deletion: {before}; after deletion: {deleted}; after restore: {restored}")
    if (before, deleted, restored) != (1, 0, 1):
        raise SystemExit("Restore verification failed")
    print("PASS: PostgreSQL data restored from backup")


if __name__ == "__main__":
    main()
