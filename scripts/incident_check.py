import argparse
import json
from pathlib import Path
import subprocess
import sys
import time

import httpx


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-laboratory-incident", action="store_true", required=True)
    args = parser.parse_args()
    if not args.allow_laboratory_incident:
        parser.error("Explicit laboratory incident flag required")
    compose = [
        "docker",
        "compose",
        "--env-file",
        "/etc/library/container.env",
        "--env-file",
        "/var/lib/library/release.env",
    ]
    base = "http://127.0.0.1:8080"
    results = {"before_health": httpx.get(base + "/health", timeout=10).status_code}
    version = httpx.get(base + "/version", timeout=10).json()["version"]
    if results["before_health"] != 200:
        raise SystemExit("Start from a healthy laboratory environment")
    try:
        subprocess.run(compose + ["stop", "db"], check=True, timeout=60)
        response = httpx.get(base + "/health", timeout=20)
        results["incident_health"] = response.status_code
        results["incident_request_id"] = response.headers.get("X-Request-ID")
        if response.status_code != 503:
            raise SystemExit("Expected database health failure")
        for _ in range(30):
            alerts = httpx.get("http://127.0.0.1:9090/api/v1/alerts", timeout=10).json()
            matching = [
                item
                for item in alerts["data"]["alerts"]
                if item["labels"].get("alertname") == "LibraryDatabaseUnavailable"
                and item["state"] == "firing"
            ]
            if matching:
                results["database_alert"] = matching[0]["state"]
                break
            time.sleep(5)
        else:
            raise SystemExit("Database alert did not fire")
        metrics = httpx.get(
            "http://127.0.0.1:9090/api/v1/query", params={"query": "min(library_database_up)"}, timeout=10
        ).json()
        results["database_metric"] = metrics["data"]["result"][0]["value"][1]
        if results["database_metric"] != "0":
            raise SystemExit("Expected database metric 0")
        logs = subprocess.run(
            compose + ["logs", "--tail", "150", "app"], capture_output=True, text=True, check=True
        )
        results["request_correlated_in_logs"] = results["incident_request_id"] in logs.stdout
        if not results["request_correlated_in_logs"]:
            raise SystemExit("Incident request missing from structured logs")
        print(json.dumps(results, indent=2), flush=True)
    finally:
        subprocess.run(compose + ["start", "db"], check=True, timeout=60)
    for _ in range(60):
        if httpx.get(base + "/health", timeout=10).status_code == 200:
            break
        time.sleep(1)
    else:
        raise SystemExit("Database did not recover")
    subprocess.run([sys.executable, "scripts/release_check.py", base, version], check=True, timeout=90)
    results["recovered_health"] = 200
    Path("artifacts").mkdir(exist_ok=True)
    Path("artifacts/incident.json").write_text(json.dumps(results, indent=2) + "\n")
    print("PASS: incident detected, correlated and recovered", flush=True)


if __name__ == "__main__":
    main()
