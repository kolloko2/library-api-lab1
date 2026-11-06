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
    response = httpx.get("http://127.0.0.1:8080/health", timeout=10)
    response.raise_for_status()
    print("Container configuration, UID and HTTP health verified")


if __name__ == "__main__":
    main()
