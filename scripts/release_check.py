import sys
import uuid
import httpx


def main():
    base, expected = sys.argv[1:]
    if not base.startswith(("http://", "https://")):
        raise SystemExit("HTTP URL required")

    def request(path, payload=None):
        response = httpx.request("POST" if payload else "GET", base + path, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()

    if request("/health")["status"] != "ok":
        raise SystemExit("Unhealthy release")
    if request("/version")["version"] != expected:
        raise SystemExit("Wrong version")
    suffix = uuid.uuid4().hex
    author = request("/authors", {"name": "release-check-" + suffix})
    if not any(item["id"] == author["id"] for item in request("/authors")):
        raise SystemExit("Database scenario failed")
    print("Release health, version and database write/read verified")


if __name__ == "__main__":
    main()
