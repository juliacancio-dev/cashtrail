"""RF-031: saldo inicial por conta."""

import pytest


def _login(client, email: str) -> dict[str, str]:
    payload = {"email": email, "password": "supersecret1"}
    client.post("/auth/register", json=payload)
    token = client.post("/auth/login", json=payload).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_opening_balance_defaults_to_zero(client):
    headers = _login(client, "ob1@example.com")

    created = client.post("/accounts", json={"name": "Corrente", "type": "checking"}, headers=headers).json()

    assert created["opening_balance"] == "0.00"


def test_create_with_opening_balance_including_negative(client):
    headers = _login(client, "ob2@example.com")

    positive = client.post(
        "/accounts", json={"name": "Poupança", "type": "savings", "opening_balance": "1500.50"}, headers=headers
    ).json()
    negative = client.post(
        "/accounts", json={"name": "No vermelho", "type": "checking", "opening_balance": "-200.00"}, headers=headers
    ).json()

    assert (positive["opening_balance"], negative["opening_balance"]) == ("1500.50", "-200.00")


def test_update_opening_balance_without_touching_the_name(client):
    headers = _login(client, "ob3@example.com")
    account = client.post("/accounts", json={"name": "Corrente", "type": "checking"}, headers=headers).json()

    updated = client.patch(f"/accounts/{account['id']}", json={"opening_balance": "999.99"}, headers=headers)

    assert updated.status_code == 200
    assert (updated.json()["name"], updated.json()["opening_balance"]) == ("Corrente", "999.99")


def test_rename_still_works_and_keeps_the_balance(client):
    headers = _login(client, "ob4@example.com")
    account = client.post(
        "/accounts", json={"name": "Corrente", "type": "checking", "opening_balance": "100.00"}, headers=headers
    ).json()

    renamed = client.patch(f"/accounts/{account['id']}", json={"name": "Itaú"}, headers=headers).json()

    assert (renamed["name"], renamed["opening_balance"]) == ("Itaú", "100.00")


@pytest.mark.parametrize("value", ["10.005", "abc", "99999999999.00"])
def test_rejects_invalid_opening_balance(client, value):
    headers = _login(client, "ob5@example.com")

    response = client.post(
        "/accounts", json={"name": "X", "type": "checking", "opening_balance": value}, headers=headers
    )

    assert response.status_code == 422


def test_other_user_cannot_change_opening_balance(client):
    owner = _login(client, "ob6owner@example.com")
    intruder = _login(client, "ob6intruder@example.com")
    account = client.post("/accounts", json={"name": "Corrente", "type": "checking"}, headers=owner).json()

    response = client.patch(f"/accounts/{account['id']}", json={"opening_balance": "1.00"}, headers=intruder)

    assert response.status_code == 404
    assert client.get(f"/accounts/{account['id']}", headers=owner).json()["opening_balance"] == "0.00"
