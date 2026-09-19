from datetime import date

from src.features.recurring import service as recurring_service


def _register_and_login(client, email: str) -> str:
    payload = {"email": email, "password": "supersecret1"}
    client.post("/auth/register", json=payload)
    response = client.post("/auth/login", json=payload)
    return response.json()["access_token"]


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _create_account(client, token: str) -> str:
    response = client.post(
        "/accounts", json={"name": "Conta Corrente", "type": "checking"}, headers=_auth_headers(token)
    )
    return response.json()["id"]


def _create_category(client, token: str, name: str = "Assinaturas") -> str:
    response = client.post("/categories", json={"name": name}, headers=_auth_headers(token))
    return response.json()["id"]


def test_create_and_list_recurring(client):
    token = _register_and_login(client, "rec1@example.com")
    account_id = _create_account(client, token)
    category_id = _create_category(client, token)

    create_response = client.post(
        "/recurring",
        json={
            "account_id": account_id,
            "category_id": category_id,
            "type": "expense",
            "amount": "29.90",
            "frequency": "monthly",
            "next_occurrence_date": "2026-10-05",
        },
        headers=_auth_headers(token),
    )
    list_response = client.get("/recurring", headers=_auth_headers(token))

    assert create_response.status_code == 201
    assert create_response.json()["is_active"] is True
    assert len(list_response.json()) == 1


def test_recurring_requires_authentication(client):
    response = client.get("/recurring")

    assert response.status_code == 401


def test_user_cannot_access_another_users_recurring(client):
    token_a = _register_and_login(client, "recusera@example.com")
    token_b = _register_and_login(client, "recuserb@example.com")
    account_id = _create_account(client, token_a)
    category_id = _create_category(client, token_a)
    created = client.post(
        "/recurring",
        json={
            "account_id": account_id,
            "category_id": category_id,
            "type": "expense",
            "amount": "10.00",
            "frequency": "weekly",
            "next_occurrence_date": "2026-10-01",
        },
        headers=_auth_headers(token_a),
    )
    recurring_id = created.json()["id"]

    response = client.get(f"/recurring/{recurring_id}", headers=_auth_headers(token_b))

    assert response.status_code == 404


def test_deactivate_recurring(client):
    token = _register_and_login(client, "recdeactivate@example.com")
    account_id = _create_account(client, token)
    category_id = _create_category(client, token)
    created = client.post(
        "/recurring",
        json={
            "account_id": account_id,
            "category_id": category_id,
            "type": "expense",
            "amount": "10.00",
            "frequency": "weekly",
            "next_occurrence_date": "2026-10-01",
        },
        headers=_auth_headers(token),
    )
    recurring_id = created.json()["id"]

    response = client.post(f"/recurring/{recurring_id}/deactivate", headers=_auth_headers(token))

    assert response.status_code == 200
    assert response.json()["is_active"] is False


def test_cannot_create_recurring_on_archived_account(client):
    token = _register_and_login(client, "recarchived@example.com")
    account_id = _create_account(client, token)
    category_id = _create_category(client, token)
    client.post(f"/accounts/{account_id}/archive", headers=_auth_headers(token))

    response = client.post(
        "/recurring",
        json={
            "account_id": account_id,
            "category_id": category_id,
            "type": "expense",
            "amount": "10.00",
            "frequency": "monthly",
            "next_occurrence_date": "2026-10-01",
        },
        headers=_auth_headers(token),
    )

    assert response.status_code == 422


def test_generate_due_transactions_creates_transaction_and_advances_date(client, db_session):
    """RF-010/RB-004: gera automaticamente o lançamento e avança para a próxima ocorrência."""
    token = _register_and_login(client, "recgen1@example.com")
    account_id = _create_account(client, token)
    category_id = _create_category(client, token)
    created = client.post(
        "/recurring",
        json={
            "account_id": account_id,
            "category_id": category_id,
            "type": "expense",
            "amount": "50.00",
            "frequency": "monthly",
            "next_occurrence_date": "2026-09-10",
        },
        headers=_auth_headers(token),
    ).json()

    generated = recurring_service.generate_due_transactions(db_session, as_of=date(2026, 9, 15))

    assert generated == 1
    transactions = client.get("/transactions", headers=_auth_headers(token)).json()
    assert len(transactions) == 1
    assert transactions[0]["source"] == "recurring"
    assert transactions[0]["recurring_transaction_id"] == created["id"]

    updated = client.get(f"/recurring/{created['id']}", headers=_auth_headers(token)).json()
    assert updated["next_occurrence_date"] == "2026-10-10"


def test_generate_due_transactions_ignores_future_and_inactive(client, db_session):
    token = _register_and_login(client, "recgen2@example.com")
    account_id = _create_account(client, token)
    category_id = _create_category(client, token)
    future = client.post(
        "/recurring",
        json={
            "account_id": account_id,
            "category_id": category_id,
            "type": "expense",
            "amount": "10.00",
            "frequency": "weekly",
            "next_occurrence_date": "2026-12-01",
        },
        headers=_auth_headers(token),
    ).json()
    due_but_inactive = client.post(
        "/recurring",
        json={
            "account_id": account_id,
            "category_id": category_id,
            "type": "expense",
            "amount": "10.00",
            "frequency": "weekly",
            "next_occurrence_date": "2026-09-01",
        },
        headers=_auth_headers(token),
    ).json()
    client.post(f"/recurring/{due_but_inactive['id']}/deactivate", headers=_auth_headers(token))

    generated = recurring_service.generate_due_transactions(db_session, as_of=date(2026, 9, 15))

    assert generated == 0
    assert client.get("/transactions", headers=_auth_headers(token)).json() == []


def test_generate_due_transactions_weekly_advances_seven_days(client, db_session):
    token = _register_and_login(client, "recgen3@example.com")
    account_id = _create_account(client, token)
    category_id = _create_category(client, token)
    created = client.post(
        "/recurring",
        json={
            "account_id": account_id,
            "category_id": category_id,
            "type": "expense",
            "amount": "15.00",
            "frequency": "weekly",
            "next_occurrence_date": "2026-09-10",
        },
        headers=_auth_headers(token),
    ).json()

    recurring_service.generate_due_transactions(db_session, as_of=date(2026, 9, 15))

    updated = client.get(f"/recurring/{created['id']}", headers=_auth_headers(token)).json()
    assert updated["next_occurrence_date"] == "2026-09-17"
