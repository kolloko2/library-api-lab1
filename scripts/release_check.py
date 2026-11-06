import sys
import uuid
import httpx


def main():
    base, expected = sys.argv[1:]
    if not base.startswith(("http://", "https://")):
        raise SystemExit("HTTP URL required")

    def request(path, payload=None):
        response = httpx.request(
            "POST" if payload is not None else "GET", base + path, json=payload, timeout=10
        )
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
    isbn = str(uuid.uuid4().int)[:13]
    book = request("/books", {"title": "Release check " + suffix, "isbn": isbn, "author_id": author["id"]})
    branch = request("/branches", {"name": "release-" + suffix, "address": "Release verification branch"})
    copy = request("/copies", {"inventory_number": suffix, "book_id": book["id"], "branch_id": branch["id"]})
    loan = request("/loans", {"copy_id": copy["id"], "reader_name": "release-" + suffix})
    duplicate = httpx.post(
        base + "/loans", json={"copy_id": copy["id"], "reader_name": "another-" + suffix}, timeout=10
    )
    if duplicate.status_code != 409:
        raise SystemExit("Duplicate loan rule failed")
    returned = request(f"/loans/{loan['id']}/return", {})
    if not returned["returned_at"]:
        raise SystemExit("Return scenario failed")
    print("PASS: release health, version, catalog, loan conflict and return")


if __name__ == "__main__":
    main()
