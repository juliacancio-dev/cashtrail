def test_register_creates_user_without_exposing_password(client):
    response = client.post(
        "/auth/register", json={"email": "new@example.com", "password": "supersecret1"}
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "new@example.com"
    assert "password" not in body
    assert "password_hash" not in body


def test_register_duplicate_email_returns_409(client):
    payload = {"email": "dup@example.com", "password": "supersecret1"}
    client.post("/auth/register", json=payload)

    response = client.post("/auth/register", json=payload)

    assert response.status_code == 409


def test_login_returns_access_token_and_sets_refresh_cookie(client):
    payload = {"email": "login@example.com", "password": "supersecret1"}
    client.post("/auth/register", json=payload)

    response = client.post("/auth/login", json=payload)

    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "cashtrail_refresh_token" in response.cookies


def test_login_with_wrong_password_returns_generic_401(client):
    client.post("/auth/register", json={"email": "wrong@example.com", "password": "supersecret1"})

    response = client.post(
        "/auth/login", json={"email": "wrong@example.com", "password": "totalmente-errada"}
    )

    assert response.status_code == 401


def test_me_requires_authentication(client):
    response = client.get("/auth/me")

    assert response.status_code == 401


def test_me_returns_current_user_with_valid_access_token(client):
    payload = {"email": "me@example.com", "password": "supersecret1"}
    client.post("/auth/register", json=payload)
    login_response = client.post("/auth/login", json=payload)
    token = login_response.json()["access_token"]

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["email"] == "me@example.com"


def test_refresh_issues_new_access_token_from_cookie(client):
    payload = {"email": "refresh@example.com", "password": "supersecret1"}
    client.post("/auth/register", json=payload)
    client.post("/auth/login", json=payload)

    response = client.post("/auth/refresh")

    assert response.status_code == 200
    assert "access_token" in response.json()


def test_refresh_without_cookie_returns_401(client):
    response = client.post("/auth/refresh")

    assert response.status_code == 401
