def _register_and_login(client, email: str) -> str:
    payload = {"email": email, "password": "supersecret1"}
    client.post("/auth/register", json=payload)
    response = client.post("/auth/login", json=payload)
    return response.json()["access_token"]


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_create_and_list_categories(client):
    token = _register_and_login(client, "cat1@example.com")

    create_response = client.post(
        "/categories", json={"name": "Mercado"}, headers=_auth_headers(token)
    )
    list_response = client.get("/categories", headers=_auth_headers(token))

    assert create_response.status_code == 201
    assert len(list_response.json()) == 1
    assert list_response.json()[0]["name"] == "Mercado"


def test_categories_require_authentication(client):
    response = client.get("/categories")

    assert response.status_code == 401


def test_user_cannot_access_another_users_category(client):
    """RNF-001: isolamento de dados por usuário."""
    token_a = _register_and_login(client, "catusera@example.com")
    token_b = _register_and_login(client, "catuserb@example.com")
    created = client.post(
        "/categories", json={"name": "Categoria A"}, headers=_auth_headers(token_a)
    )
    category_id = created.json()["id"]

    response = client.get(f"/categories/{category_id}", headers=_auth_headers(token_b))

    assert response.status_code == 404


def test_archive_category_marks_as_archived(client):
    token = _register_and_login(client, "catarchive@example.com")
    created = client.post(
        "/categories", json={"name": "Lazer"}, headers=_auth_headers(token)
    )
    category_id = created.json()["id"]

    response = client.post(f"/categories/{category_id}/archive", headers=_auth_headers(token))

    assert response.status_code == 200
    assert response.json()["is_archived"] is True


def test_get_nonexistent_category_returns_404(client):
    token = _register_and_login(client, "catnotfound@example.com")

    response = client.get(
        "/categories/00000000-0000-0000-0000-000000000000", headers=_auth_headers(token)
    )

    assert response.status_code == 404
