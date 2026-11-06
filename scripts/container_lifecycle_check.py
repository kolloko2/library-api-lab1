import argparse
import json
import os
from pathlib import Path
import secrets
import subprocess
import time
import uuid

import httpx


def run(*args, **kwargs):
    return subprocess.run(args, check=True, capture_output=True, **kwargs).stdout


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", default=".env")
    args = parser.parse_args()
    compose = ["docker", "compose", "--env-file", args.env_file]
    marker = "persistence-" + uuid.uuid4().hex
    base = "http://127.0.0.1:8080"
    response = httpx.post(base + "/authors", json={"name": marker}, timeout=10)
    response.raise_for_status()
    author_id = response.json()["id"]
    run(*compose, "up", "-d", "--no-deps", "--force-recreate", "--wait", "db", "app")
    run(*compose, "exec", "-T", "nginx", "nginx", "-s", "reload")
    response = httpx.get(base + "/authors", timeout=10)
    response.raise_for_status()
    if not any(row["id"] == author_id and row["name"] == marker for row in response.json()):
        raise SystemExit("Data lost after recreation")
    print("PASS: record preserved after application and database recreation", flush=True)
    app_id = run(*compose, "ps", "-q", "app").decode().strip()
    run(*compose, "stop", "-t", "20", "app")
    exit_code = run("docker", "inspect", "--format", "{{.State.ExitCode}}", app_id).decode().strip()
    if exit_code != "0":
        raise SystemExit("Application did not stop gracefully: " + exit_code)
    print("PASS: graceful SIGTERM shutdown, exit code " + exit_code, flush=True)
    run(*compose, "up", "-d", "--no-deps", "--wait", "app")
    run(*compose, "exec", "-T", "nginx", "nginx", "-s", "reload")
    backup = run(*compose, "exec", "-T", "db", "pg_dump", "-U", "library", "-d", "library", "-Fc")
    Path("artifacts").mkdir(exist_ok=True)
    Path("artifacts/container.dump").write_bytes(backup)
    name = "library-restore-check-" + uuid.uuid4().hex[:12]
    env = dict(os.environ, POSTGRES_PASSWORD=secrets.token_hex(24))
    run("docker", "volume", "create", name)
    started = False
    try:
        run(
            "docker",
            "run",
            "-d",
            "--name",
            name,
            "--network",
            "none",
            "-e",
            "POSTGRES_PASSWORD",
            "-e",
            "POSTGRES_USER=library",
            "-e",
            "POSTGRES_DB=library",
            "-v",
            name + ":/var/lib/postgresql/data",
            "postgres:16.10-bookworm",
            env=env,
        )
        started = True
        for _ in range(60):
            result = subprocess.run(
                ["docker", "exec", name, "pg_isready", "-U", "library"], capture_output=True
            )
            if result.returncode == 0:
                break
            time.sleep(1)
        else:
            raise SystemExit("Restore database did not start")
        run(
            "docker",
            "exec",
            "-i",
            name,
            "pg_restore",
            "-U",
            "library",
            "-d",
            "library",
            "--no-owner",
            "--exit-on-error",
            input=backup,
        )
        count = (
            run(
                "docker",
                "exec",
                "-i",
                name,
                "psql",
                "-U",
                "library",
                "-d",
                "library",
                "-At",
                "-v",
                "marker=" + marker,
                input=b"SELECT count(*) FROM authors WHERE name=:'marker';\n",
            )
            .decode()
            .strip()
        )
        if count != "1":
            raise SystemExit("Restored record missing")
        print("PASS: PostgreSQL backup restored into a new volume", flush=True)
    finally:
        if started:
            run("docker", "stop", name)
            run("docker", "rm", name)
        run("docker", "volume", "rm", name)
    Path("artifacts/container-lifecycle.json").write_text(
        json.dumps(
            {
                "preserved_author_id": author_id,
                "graceful_exit_code": int(exit_code),
                "restored_count": int(count),
            },
            indent=2,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
