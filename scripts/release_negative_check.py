import argparse
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

import httpx


def command(*args, env=None):
    return subprocess.run(args, capture_output=True, text=True, timeout=90, env=env)


def require_rejected(result, scenario):
    if result.returncode == 0:
        raise SystemExit(f"Unsafe acceptance: {scenario}")
    print(f"PASS: rejected {scenario}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)
    parser.add_argument("--version", required=True)
    args = parser.parse_args()
    if not args.image.startswith("127.0.0.1:5000/library:"):
        parser.error("Use a previously accepted image from the laboratory registry")
    command("docker", "image", "inspect", args.image).check_returncode()
    results = {}
    env = dict(os.environ)
    env.pop("DB_PASSWORD", None)
    require_rejected(
        command("docker", "compose", "--env-file", "/dev/null", "config", "--quiet", env=env),
        "missing DB_PASSWORD",
    )
    results["missing_variable"] = "rejected"
    httpx.get("http://127.0.0.1:5000/v2/", timeout=5).raise_for_status()
    require_rejected(
        command("docker", "pull", "127.0.0.1:5000/library:missing-" + uuid.uuid4().hex),
        "unknown registry tag",
    )
    results["unknown_tag"] = "rejected"
    require_rejected(command("docker", "pull", "127.0.0.1:5999/library:unavailable"), "unavailable registry")
    results["unavailable_registry"] = "rejected"
    with open("/var/lock/library-deploy.lock", "a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        rejected = command("/usr/local/sbin/library-deploy", args.version)
        require_rejected(rejected, "concurrent deployment")
        if "Deployment already in progress" not in rejected.stderr:
            raise SystemExit("Expected deployment lock rejection")
    results["concurrent_deployment"] = "rejected"
    for scenario in ("healthcheck", "business_scenario"):
        name = "library-negative-" + uuid.uuid4().hex[:12]
        try:
            options = [
                "docker",
                "run",
                "-d",
                "--name",
                name,
                "--memory",
                "256m",
                "--cpus",
                "0.5",
                "-p",
                "127.0.0.1:18081:8000",
                "-e",
                "DATABASE_URL=sqlite:////tmp/candidate.db",
                "-e",
                "APP_VERSION=" + args.version,
                "--health-interval",
                "1s",
                "--health-retries",
                "1",
            ]
            if scenario == "healthcheck":
                options += ["--health-cmd", "exit 1"]
            else:
                options += ["-e", "MAX_ACTIVE_LOANS=0"]
            options += [
                args.image,
                "sh",
                "-c",
                "python -m alembic upgrade head && exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8000",
            ]
            command(*options).check_returncode()
            for _ in range(60):
                try:
                    ready = httpx.get("http://127.0.0.1:18081/health", timeout=1).status_code == 200
                except httpx.HTTPError:
                    ready = False
                if ready:
                    break
                time.sleep(1)
            else:
                raise SystemExit("Candidate did not start")
            if scenario == "healthcheck":
                state = command("docker", "inspect", "--format", "{{.State.Health.Status}}", name)
                if state.stdout.strip() != "unhealthy":
                    raise SystemExit("Expected failed container healthcheck")
                print("PASS: rejected unhealthy candidate despite HTTP 200")
            else:
                require_rejected(
                    command(
                        sys.executable, "scripts/release_check.py", "http://127.0.0.1:18081", args.version
                    ),
                    "broken loan scenario despite HTTP 200",
                )
            results[scenario] = "rejected"
        finally:
            command("docker", "rm", "-f", name)
    Path("artifacts").mkdir(exist_ok=True)
    Path("artifacts/release-negative.json").write_text(json.dumps(results, indent=2) + "\n")
    print("PASS: all six negative release checks")


if __name__ == "__main__":
    main()
