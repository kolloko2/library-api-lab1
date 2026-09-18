def seed_copy(client):
    client.post("/authors", json={"name": "Лев Толстой"})
    client.post(
        "/books",
        json={"title": "Война и мир", "isbn": "9785170906436", "author_id": 1},
    )
    client.post(
        "/branches", json={"name": "Филиал №1", "address": "проспект Мира, 1"}
    )
    response = client.post(
        "/copies", json={"inventory_number": "COPY-001", "book_id": 1, "branch_id": 1}
    )
    assert response.status_code == 201


def test_loan_and_return_business_rule(client):
    seed_copy(client)

    loan = client.post("/loans", json={"copy_id": 1, "reader_name": "Иван Петров"})
    assert loan.status_code == 201
    assert loan.json()["returned_at"] is None

    duplicate = client.post("/loans", json={"copy_id": 1, "reader_name": "Мария Иванова"})
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == "Экземпляр уже выдан"

    returned = client.post(f"/loans/{loan.json()['id']}/return")
    assert returned.status_code == 200
    assert returned.json()["returned_at"] is not None

    repeated_return = client.post(f"/loans/{loan.json()['id']}/return")
    assert repeated_return.status_code == 409

    next_loan = client.post("/loans", json={"copy_id": 1, "reader_name": "Мария Иванова"})
    assert next_loan.status_code == 201


def test_loan_unknown_copy(client):
    response = client.post("/loans", json={"copy_id": 999, "reader_name": "Иван Петров"})
    assert response.status_code == 404

