def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_catalog_flow_and_validation(client):
    author = client.post("/authors", json={"name": "Михаил Булгаков"})
    assert author.status_code == 201

    book = client.post(
        "/books",
        json={"title": "Мастер и Маргарита", "isbn": "9785170906306", "author_id": 1},
    )
    assert book.status_code == 201

    branch = client.post(
        "/branches", json={"name": "Центральный", "address": "ул. Пушкина, 10"}
    )
    assert branch.status_code == 201

    copy = client.post(
        "/copies", json={"inventory_number": "INV-001", "book_id": 1, "branch_id": 1}
    )
    assert copy.status_code == 201
    assert copy.json()["is_available"] is True

    duplicate = client.post("/authors", json={"name": "Михаил Булгаков"})
    assert duplicate.status_code == 409

    invalid = client.post(
        "/books", json={"title": "X", "isbn": "bad-isbn", "author_id": 999}
    )
    assert invalid.status_code == 422

