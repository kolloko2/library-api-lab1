import argparse
import json
from pathlib import Path
import subprocess
import time

import httpx


def run(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout.strip()


def instance():
    response = httpx.get("http://127.0.0.1:8080/version", timeout=5)
    response.raise_for_status()
    return response.json()["instance"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", default=".env")
    args = parser.parse_args()
    ids = run("docker", "compose", "--env-file", args.env_file, "ps", "-q", "app").splitlines()
    if len(ids) != 2:
        raise SystemExit("Exactly two application replicas required")
    before = {instance() for _ in range(20)}
    if len(before) != 2:
        raise SystemExit("Nginx did not distribute requests between two replicas")
    print("Before failure:", ", ".join(sorted(before)), flush=True)
    run("docker", "stop", "--time", "20", ids[0])
    try:
        during = {instance() for _ in range(10)}
        if len(during) != 1 or not during.issubset(before):
            raise SystemExit("Unexpected failover response")
        print("During failure: 10/10 successful requests from " + next(iter(during)), flush=True)
    finally:
        run("docker", "start", ids[0])
    recovered = set()
    for _ in range(40):
        recovered.add(instance())
        if recovered == before:
            break
        time.sleep(1)
    if recovered != before:
        raise SystemExit("Replica did not return to rotation")
    print("PASS: both replicas restored to rotation", flush=True)
    Path("artifacts").mkdir(exist_ok=True)
    Path("artifacts/failover.json").write_text(
        json.dumps(
            {
                "before": sorted(before),
                "during": sorted(during),
                "successful_during_failure": 10,
                "recovered": sorted(recovered),
            },
            indent=2,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
