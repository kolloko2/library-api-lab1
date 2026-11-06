from tests.test_loans import seed_copy


def test_active_limit(client):
    seed_copy(client)
    for number in range(2, 7):
        assert (
            client.post(
                "/copies", json={"inventory_number": f"COPY-{number}", "book_id": 1, "branch_id": 1}
            ).status_code
            == 201
        )
    for copy_id in range(1, 6):
        assert (
            client.post("/loans", json={"copy_id": copy_id, "reader_name": "Reader boundary"}).status_code
            == 201
        )
    assert client.post("/loans", json={"copy_id": 6, "reader_name": "Reader boundary"}).status_code == 409
    assert client.post("/loans/1/return").status_code == 200
    assert client.post("/loans", json={"copy_id": 6, "reader_name": "Reader boundary"}).status_code == 201


def test_missing_references_and_invalid_payloads(client):
    assert client.post("/authors", json={"name": ""}).status_code == 422
    assert (
        client.post("/books", json={"title": "Title", "isbn": "1234567890", "author_id": 999}).status_code
        == 404
    )
    assert (
        client.post(
            "/copies", json={"inventory_number": "ID-1", "book_id": 999, "branch_id": 999}
        ).status_code
        == 404
    )
    assert client.post("/loans/999/return").status_code == 404
    assert client.get("/books?author_id=-1").status_code == 422
