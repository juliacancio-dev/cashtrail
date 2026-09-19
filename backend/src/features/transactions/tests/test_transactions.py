def _register_and_login(client, email: str) -> str:
    payload = {"email": email, "password": "supersecret1"}
    client.post("/auth/register", json=payload)
    response = client.post("/auth/login", json=payload)
    return response.json()["access_token"]


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _create_account(client, token: str, name: str = "Conta Corrente") -> str:
    response = client.post(
        "/accounts", json={"name": name, "type": "checking"}, headers=_auth_headers(token)
    )
    return response.json()["id"]


def _create_category(client, token: str, name: str = "Mercado") -> str:
    response = client.post("/categories", json={"name": name}, headers=_auth_headers(token))
    return response.json()["id"]


def test_create_and_list_transactions(client):
    token = _register_and_login(client, "tx1@example.com")
    account_id = _create_account(client, token)
    category_id = _create_category(client, token)

    create_response = client.post(
        "/transactions",
        json={
            "account_id": account_id,
            "category_id": category_id,
            "type": "expense",
            "amount": "150.50",
            "description": "Compras do mes",
            "occurred_at": "2026-09-10",
        },
        headers=_auth_headers(token),
    )
    list_response = client.get("/transactions", headers=_auth_headers(token))

    assert create_response.status_code == 201
    assert create_response.json()["amount"] == "150.50"
    assert len(list_response.json()) == 1


def test_transactions_require_authentication(client):
    response = client.get("/transactions")

    assert response.status_code == 401


def test_user_cannot_access_another_users_transaction(client):
    """RNF-001: isolamento de dados por usuário."""
    token_a = _register_and_login(client, "txusera@example.com")
    token_b = _register_and_login(client, "txuserb@example.com")
    account_id = _create_account(client, token_a)
    category_id = _create_category(client, token_a)
    created = client.post(
        "/transactions",
        json={
            "account_id": account_id,
            "category_id": category_id,
            "type": "income",
            "amount": "100.00",
            "occurred_at": "2026-09-10",
        },
        headers=_auth_headers(token_a),
    )
    transaction_id = created.json()["id"]

    response = client.get(f"/transactions/{transaction_id}", headers=_auth_headers(token_b))

    assert response.status_code == 404


def test_cannot_use_another_users_account(client):
    """RB-001: lançamento só pode usar conta do próprio usuário."""
    token_a = _register_and_login(client, "txaccounta@example.com")
    token_b = _register_and_login(client, "txaccountb@example.com")
    account_id = _create_account(client, token_a)
    category_id = _create_category(client, token_b)

    response = client.post(
        "/transactions",
        json={
            "account_id": account_id,
            "category_id": category_id,
            "type": "expense",
            "amount": "50.00",
            "occurred_at": "2026-09-10",
        },
        headers=_auth_headers(token_b),
    )

    assert response.status_code == 404


def test_cannot_use_another_users_category(client):
    """RB-001: lançamento só pode usar categoria do próprio usuário."""
    token_a = _register_and_login(client, "txcata@example.com")
    token_b = _register_and_login(client, "txcatb@example.com")
    account_id = _create_account(client, token_b)
    category_id = _create_category(client, token_a)

    response = client.post(
        "/transactions",
        json={
            "account_id": account_id,
            "category_id": category_id,
            "type": "expense",
            "amount": "50.00",
            "occurred_at": "2026-09-10",
        },
        headers=_auth_headers(token_b),
    )

    assert response.status_code == 404


def test_cannot_create_transaction_on_archived_account(client):
    """RB-003 (10-data-model.md): conta arquivada não aceita novos lançamentos."""
    token = _register_and_login(client, "txarchived@example.com")
    account_id = _create_account(client, token)
    category_id = _create_category(client, token)
    client.post(f"/accounts/{account_id}/archive", headers=_auth_headers(token))

    response = client.post(
        "/transactions",
        json={
            "account_id": account_id,
            "category_id": category_id,
            "type": "expense",
            "amount": "50.00",
            "occurred_at": "2026-09-10",
        },
        headers=_auth_headers(token),
    )

    assert response.status_code == 422


def test_amount_must_be_positive(client):
    """Invariante do 10-data-model.md: amount > 0 sempre; direção vem do type."""
    token = _register_and_login(client, "txnegative@example.com")
    account_id = _create_account(client, token)
    category_id = _create_category(client, token)

    response = client.post(
        "/transactions",
        json={
            "account_id": account_id,
            "category_id": category_id,
            "type": "expense",
            "amount": "-10.00",
            "occurred_at": "2026-09-10",
        },
        headers=_auth_headers(token),
    )

    assert response.status_code == 422


def test_list_transactions_filters_by_period(client):
    token = _register_and_login(client, "txperiod@example.com")
    account_id = _create_account(client, token)
    category_id = _create_category(client, token)
    for occurred_at in ["2026-08-15", "2026-09-10", "2026-10-01"]:
        client.post(
            "/transactions",
            json={
                "account_id": account_id,
                "category_id": category_id,
                "type": "expense",
                "amount": "10.00",
                "occurred_at": occurred_at,
            },
            headers=_auth_headers(token),
        )

    response = client.get(
        "/transactions",
        params={"start_date": "2026-09-01", "end_date": "2026-09-30"},
        headers=_auth_headers(token),
    )

    assert len(response.json()) == 1
    assert response.json()[0]["occurred_at"] == "2026-09-10"
