import json
import subprocess
import httpx


def run(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout.strip()


def main():
    run("docker", "compose", "config", "--quiet")
    run("docker", "compose", "up", "-d", "--build", "--wait", "--wait-timeout", "180")
    uid = run("docker", "compose", "exec", "-T", "app", "id", "-u")
    if uid == "0":
        raise SystemExit("Application runs as root")
    app_id = run("docker", "compose", "ps", "-q", "app")
    details = json.loads(run("docker", "inspect", app_id))[0]
    if details["State"]["Health"]["Status"] != "healthy":
        raise SystemExit("Application healthcheck failed")
    if not details["HostConfig"]["Memory"] or not details["HostConfig"]["NanoCpus"]:
        raise SystemExit("Application resource limits are required")
    db_id = run("docker", "compose", "ps", "-q", "db")
    database = json.loads(run("docker", "inspect", db_id))[0]
    if any(database["NetworkSettings"]["Ports"].values()):
        raise SystemExit("Database ports must remain private")
    if not any(mount["Type"] == "volume" for mount in database["Mounts"]):
        raise SystemExit("Database persistent volume is required")
    response = httpx.get("http://127.0.0.1:8080/health", timeout=10)
    response.raise_for_status()
    print("Container configuration, UID, limits, health, private DB and volume verified")


if __name__ == "__main__":
    main()
