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


def _create_category(client, token: str, name: str = "Mercado") -> str:
    response = client.post("/categories", json={"name": name}, headers=_auth_headers(token))
    return response.json()["id"]


def _create_transaction(client, token, account_id, category_id, amount, occurred_at):
    return client.post(
        "/transactions",
        json={
            "account_id": account_id,
            "category_id": category_id,
            "type": "expense",
            "amount": amount,
            "occurred_at": occurred_at,
        },
        headers=_auth_headers(token),
    )


def test_create_and_list_budgets(client):
    token = _register_and_login(client, "budget1@example.com")
    category_id = _create_category(client, token)

    create_response = client.post(
        "/budgets",
        json={"category_id": category_id, "month": "2026-09", "limit_amount": "500.00"},
        headers=_auth_headers(token),
    )
    list_response = client.get("/budgets", headers=_auth_headers(token))

    assert create_response.status_code == 201
    assert create_response.json()["spent_amount"] == "0"
    assert create_response.json()["is_exceeded"] is False
    assert len(list_response.json()) == 1


def test_budgets_require_authentication(client):
    response = client.get("/budgets")

    assert response.status_code == 401


def test_duplicate_budget_for_same_category_and_month_is_rejected(client):
    """RB-002."""
    token = _register_and_login(client, "budgetdup@example.com")
    category_id = _create_category(client, token)
    client.post(
        "/budgets",
        json={"category_id": category_id, "month": "2026-09", "limit_amount": "500.00"},
        headers=_auth_headers(token),
    )

    response = client.post(
        "/budgets",
        json={"category_id": category_id, "month": "2026-09", "limit_amount": "300.00"},
        headers=_auth_headers(token),
    )

    assert response.status_code == 409


def test_budget_tracks_spending_live(client):
    """RF-007: orçamento mostra % consumido em tempo real conforme lançamentos são criados."""
    token = _register_and_login(client, "budgettrack@example.com")
    account_id = _create_account(client, token)
    category_id = _create_category(client, token)
    budget = client.post(
        "/budgets",
        json={"category_id": category_id, "month": "2026-09", "limit_amount": "200.00"},
        headers=_auth_headers(token),
    ).json()

    _create_transaction(client, token, account_id, category_id, "50.00", "2026-09-05")
    _create_transaction(client, token, account_id, category_id, "100.00", "2026-09-10")

    response = client.get(f"/budgets/{budget['id']}", headers=_auth_headers(token))

    assert response.json()["spent_amount"] == "150.00"
    assert response.json()["percent_consumed"] == "75.00"
    assert response.json()["is_exceeded"] is False


def test_budget_flags_exceeded_when_over_limit(client):
    """RF-008: sinaliza quando o orçamento é ultrapassado."""
    token = _register_and_login(client, "budgetexceed@example.com")
    account_id = _create_account(client, token)
    category_id = _create_category(client, token)
    budget = client.post(
        "/budgets",
        json={"category_id": category_id, "month": "2026-09", "limit_amount": "100.00"},
        headers=_auth_headers(token),
    ).json()

    _create_transaction(client, token, account_id, category_id, "150.00", "2026-09-05")

    response = client.get(f"/budgets/{budget['id']}", headers=_auth_headers(token))

    assert response.json()["is_exceeded"] is True


def test_budget_ignores_spending_outside_its_month(client):
    token = _register_and_login(client, "budgetperiod@example.com")
    account_id = _create_account(client, token)
    category_id = _create_category(client, token)
    budget = client.post(
        "/budgets",
        json={"category_id": category_id, "month": "2026-09", "limit_amount": "100.00"},
        headers=_auth_headers(token),
    ).json()

    _create_transaction(client, token, account_id, category_id, "999.00", "2026-08-31")

    response = client.get(f"/budgets/{budget['id']}", headers=_auth_headers(token))

    assert response.json()["spent_amount"] == "0"


def test_user_cannot_access_another_users_budget(client):
    token_a = _register_and_login(client, "budgetusera@example.com")
    token_b = _register_and_login(client, "budgetuserb@example.com")
    category_id = _create_category(client, token_a)
    budget = client.post(
        "/budgets",
        json={"category_id": category_id, "month": "2026-09", "limit_amount": "100.00"},
        headers=_auth_headers(token_a),
    ).json()

    response = client.get(f"/budgets/{budget['id']}", headers=_auth_headers(token_b))

    assert response.status_code == 404


def test_update_and_delete_budget(client):
    token = _register_and_login(client, "budgetupdate@example.com")
    category_id = _create_category(client, token)
    budget = client.post(
        "/budgets",
        json={"category_id": category_id, "month": "2026-09", "limit_amount": "100.00"},
        headers=_auth_headers(token),
    ).json()

    updated = client.patch(
        f"/budgets/{budget['id']}", json={"limit_amount": "250.00"}, headers=_auth_headers(token)
    )
    deleted = client.delete(f"/budgets/{budget['id']}", headers=_auth_headers(token))
    get_after_delete = client.get(f"/budgets/{budget['id']}", headers=_auth_headers(token))

    assert updated.status_code == 200
    assert updated.json()["limit_amount"] == "250.00"
    assert deleted.status_code == 204
    assert get_after_delete.status_code == 404
