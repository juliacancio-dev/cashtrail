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


def _create_category(client, token: str, name: str) -> str:
    response = client.post("/categories", json={"name": name}, headers=_auth_headers(token))
    return response.json()["id"]


def _create_transaction(client, token, account_id, category_id, type, amount, occurred_at):
    return client.post(
        "/transactions",
        json={
            "account_id": account_id,
            "category_id": category_id,
            "type": type,
            "amount": amount,
            "occurred_at": occurred_at,
        },
        headers=_auth_headers(token),
    )


def test_dashboard_summary_matches_manual_sum(client):
    """RF-006: soma exibida bate com soma manual dos lançamentos do período."""
    token = _register_and_login(client, "dash1@example.com")
    account_id = _create_account(client, token)
    market = _create_category(client, token, "Mercado")
    salary = _create_category(client, token, "Salario")

    _create_transaction(client, token, account_id, salary, "income", "3000.00", "2026-09-05")
    _create_transaction(client, token, account_id, market, "expense", "150.00", "2026-09-10")
    _create_transaction(client, token, account_id, market, "expense", "50.00", "2026-09-15")

    response = client.get(
        "/dashboard",
        params={"start_date": "2026-09-01", "end_date": "2026-09-30"},
        headers=_auth_headers(token),
    )

    body = response.json()
    assert response.status_code == 200
    assert body["summary"]["income_total"] == "3000.00"
    assert body["summary"]["expense_total"] == "200.00"
    assert body["summary"]["balance"] == "2800.00"


def test_dashboard_groups_spending_by_category(client):
    token = _register_and_login(client, "dash2@example.com")
    account_id = _create_account(client, token)
    market = _create_category(client, token, "Mercado")
    transport = _create_category(client, token, "Transporte")

    _create_transaction(client, token, account_id, market, "expense", "100.00", "2026-09-05")
    _create_transaction(client, token, account_id, market, "expense", "50.00", "2026-09-06")
    _create_transaction(client, token, account_id, transport, "expense", "30.00", "2026-09-07")

    response = client.get(
        "/dashboard",
        params={"start_date": "2026-09-01", "end_date": "2026-09-30"},
        headers=_auth_headers(token),
    )

    by_category = {c["category_name"]: c["total"] for c in response.json()["by_category"]}
    assert by_category == {"Mercado": "150.00", "Transporte": "30.00"}


def test_dashboard_ignores_transactions_outside_period(client):
    token = _register_and_login(client, "dash3@example.com")
    account_id = _create_account(client, token)
    category_id = _create_category(client, token, "Mercado")

    _create_transaction(client, token, account_id, category_id, "expense", "999.00", "2026-08-31")
    _create_transaction(client, token, account_id, category_id, "expense", "10.00", "2026-09-15")

    response = client.get(
        "/dashboard",
        params={"start_date": "2026-09-01", "end_date": "2026-09-30"},
        headers=_auth_headers(token),
    )

    assert response.json()["summary"]["expense_total"] == "10.00"


def test_dashboard_requires_authentication(client):
    response = client.get("/dashboard")

    assert response.status_code == 401


def test_dashboard_defaults_to_current_month_when_no_period_given(client):
    token = _register_and_login(client, "dash4@example.com")

    response = client.get("/dashboard", headers=_auth_headers(token))

    assert response.status_code == 200
    assert response.json()["summary"]["balance"] == "0"
