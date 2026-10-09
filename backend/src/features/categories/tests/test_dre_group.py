"""RF-032: grupo de DRE nas categorias."""

import pytest


def _login(client, email: str) -> dict[str, str]:
    payload = {"email": email, "password": "supersecret1"}
    client.post("/auth/register", json=payload)
    token = client.post("/auth/login", json=payload).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_category_starts_without_group(client):
    headers = _login(client, "dg1@example.com")

    created = client.post("/categories", json={"name": "Mercado"}, headers=headers).json()

    assert created["dre_group"] is None


@pytest.mark.parametrize(
    "group", ["revenue", "deduction", "variable_expense", "fixed_expense", "financial_expense", "financial_revenue"]
)
def test_create_with_each_valid_group(client, group):
    headers = _login(client, f"dg2{group}@example.com")

    created = client.post("/categories", json={"name": "Cat", "dre_group": group}, headers=headers)

    assert created.status_code == 201
    assert created.json()["dre_group"] == group


def test_invalid_group_is_rejected(client):
    headers = _login(client, "dg3@example.com")
    created = client.post("/categories", json={"name": "Cat"}, headers=headers).json()

    on_create = client.post("/categories", json={"name": "X", "dre_group": "outro"}, headers=headers)
    on_update = client.patch(f"/categories/{created['id']}", json={"dre_group": "outro"}, headers=headers)

    assert (on_create.status_code, on_update.status_code) == (422, 422)


def test_set_change_and_clear_group_without_renaming(client):
    headers = _login(client, "dg4@example.com")
    category = client.post("/categories", json={"name": "Aluguel"}, headers=headers).json()

    set_ = client.patch(f"/categories/{category['id']}", json={"dre_group": "fixed_expense"}, headers=headers).json()
    changed = client.patch(f"/categories/{category['id']}", json={"dre_group": "variable_expense"}, headers=headers).json()
    cleared = client.patch(f"/categories/{category['id']}", json={"dre_group": None}, headers=headers).json()

    assert [c["dre_group"] for c in (set_, changed, cleared)] == ["fixed_expense", "variable_expense", None]
    assert {c["name"] for c in (set_, changed, cleared)} == {"Aluguel"}


def test_rename_keeps_group(client):
    headers = _login(client, "dg5@example.com")
    category = client.post("/categories", json={"name": "Luz", "dre_group": "fixed_expense"}, headers=headers).json()

    renamed = client.patch(f"/categories/{category['id']}", json={"name": "Energia"}, headers=headers).json()

    assert (renamed["name"], renamed["dre_group"]) == ("Energia", "fixed_expense")


def test_other_user_cannot_change_group(client):
    owner = _login(client, "dg6owner@example.com")
    intruder = _login(client, "dg6intruder@example.com")
    category = client.post("/categories", json={"name": "Luz"}, headers=owner).json()

    response = client.patch(f"/categories/{category['id']}", json={"dre_group": "fixed_expense"}, headers=intruder)

    assert response.status_code == 404
    assert client.get(f"/categories/{category['id']}", headers=owner).json()["dre_group"] is None
