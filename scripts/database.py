"""Explicit backup/restore command; stop application writers before restoring."""

import argparse
import os
from pathlib import Path
import sqlite3
import subprocess

from sqlalchemy.engine import make_url


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["backup", "restore"])
    parser.add_argument("file", type=Path)
    args = parser.parse_args()
    url = make_url(os.environ.get("DATABASE_URL", "sqlite:///library.db"))
    if url.drivername.startswith("sqlite"):
        source, target = (
            (url.database, str(args.file)) if args.action == "backup" else (str(args.file), url.database)
        )
        if not Path(source).is_file() or Path(source).resolve() == Path(target).resolve():
            raise SystemExit("Source must exist and differ from destination")
        with sqlite3.connect(source) as src, sqlite3.connect(target) as dst:
            if src.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise SystemExit("Backup integrity check failed")
            src.backup(dst)
    else:
        env = dict(os.environ, PGPASSWORD=url.password or "")
        common = [
            "--host",
            url.host,
            "--port",
            str(url.port or 5432),
            "--username",
            url.username,
            "--dbname",
            url.database,
        ]
        command = (
            ["pg_dump", "--format=custom", "--file", str(args.file)] + common
            if args.action == "backup"
            else ["pg_restore", "--clean", "--if-exists", "--no-owner", "--exit-on-error"]
            + common
            + [str(args.file)]
        )
        subprocess.run(command, env=env, check=True)


if __name__ == "__main__":
    main()
