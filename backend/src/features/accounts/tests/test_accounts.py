def _register_and_login(client, email: str) -> str:
    payload = {"email": email, "password": "supersecret1"}
    client.post("/auth/register", json=payload)
    response = client.post("/auth/login", json=payload)
    return response.json()["access_token"]


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_create_and_list_accounts(client):
    token = _register_and_login(client, "acc1@example.com")

    create_response = client.post(
        "/accounts", json={"name": "Conta Corrente", "type": "checking"}, headers=_auth_headers(token)
    )
    list_response = client.get("/accounts", headers=_auth_headers(token))

    assert create_response.status_code == 201
    assert len(list_response.json()) == 1
    assert list_response.json()[0]["name"] == "Conta Corrente"


def test_accounts_require_authentication(client):
    response = client.get("/accounts")

    assert response.status_code == 401


def test_user_cannot_access_another_users_account(client):
    """RNF-001: isolamento de dados por usuário."""
    token_a = _register_and_login(client, "usera@example.com")
    token_b = _register_and_login(client, "userb@example.com")
    created = client.post(
        "/accounts", json={"name": "Conta A", "type": "checking"}, headers=_auth_headers(token_a)
    )
    account_id = created.json()["id"]

    response = client.get(f"/accounts/{account_id}", headers=_auth_headers(token_b))

    assert response.status_code == 404


def test_archive_account_marks_as_archived(client):
    token = _register_and_login(client, "archive@example.com")
    created = client.post(
        "/accounts", json={"name": "Conta X", "type": "savings"}, headers=_auth_headers(token)
    )
    account_id = created.json()["id"]

    response = client.post(f"/accounts/{account_id}/archive", headers=_auth_headers(token))

    assert response.status_code == 200
    assert response.json()["is_archived"] is True


def test_get_nonexistent_account_returns_404(client):
    token = _register_and_login(client, "notfound@example.com")

    response = client.get(
        "/accounts/00000000-0000-0000-0000-000000000000", headers=_auth_headers(token)
    )

    assert response.status_code == 404
