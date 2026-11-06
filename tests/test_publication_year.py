def test_publication_year_is_stored_and_validated(client):
    author = client.post("/authors", json={"name": "Publication author"}).json()
    payload = {
        "title": "Year example",
        "isbn": "1234567890",
        "author_id": author["id"],
        "publication_year": 2026,
    }
    response = client.post("/books", json=payload)
    assert response.status_code == 201
    assert response.json()["publication_year"] == 2026
    assert client.get("/books").json()[0]["publication_year"] == 2026
    payload["publication_year"] = 0
    assert client.post("/books", json=payload).status_code == 422
