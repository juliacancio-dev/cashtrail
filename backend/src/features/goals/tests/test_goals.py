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


def _create_category(client, token: str, name: str = "Poupanca") -> str:
    response = client.post("/categories", json={"name": name}, headers=_auth_headers(token))
    return response.json()["id"]


def test_create_and_list_goals(client):
    token = _register_and_login(client, "goal1@example.com")

    create_response = client.post(
        "/goals", json={"name": "Viagem", "target_amount": "5000.00"}, headers=_auth_headers(token)
    )
    list_response = client.get("/goals", headers=_auth_headers(token))

    assert create_response.status_code == 201
    assert create_response.json()["current_amount"] == "0"
    assert create_response.json()["percent_achieved"] == "0.00"
    assert create_response.json()["is_achieved"] is False
    assert len(list_response.json()) == 1


def test_goals_require_authentication(client):
    response = client.get("/goals")

    assert response.status_code == 401


def test_user_cannot_access_another_users_goal(client):
    token_a = _register_and_login(client, "goalusera@example.com")
    token_b = _register_and_login(client, "goaluserb@example.com")
    created = client.post(
        "/goals", json={"name": "Meta A", "target_amount": "1000.00"}, headers=_auth_headers(token_a)
    )
    goal_id = created.json()["id"]

    response = client.get(f"/goals/{goal_id}", headers=_auth_headers(token_b))

    assert response.status_code == 404


def test_contribution_updates_progress(client):
    """RB-003: progresso = soma dos lançamentos vinculados à meta."""
    token = _register_and_login(client, "goalcontrib@example.com")
    account_id = _create_account(client, token)
    category_id = _create_category(client, token)
    goal = client.post(
        "/goals", json={"name": "Reserva", "target_amount": "1000.00"}, headers=_auth_headers(token)
    ).json()

    contribution = client.post(
        f"/goals/{goal['id']}/contributions",
        json={
            "account_id": account_id,
            "category_id": category_id,
            "type": "expense",
            "amount": "400.00",
            "occurred_at": "2026-09-10",
        },
        headers=_auth_headers(token),
    )

    assert contribution.status_code == 201
    assert contribution.json()["goal_id"] == goal["id"]

    updated_goal = client.get(f"/goals/{goal['id']}", headers=_auth_headers(token)).json()
    assert updated_goal["current_amount"] == "400.00"
    assert updated_goal["percent_achieved"] == "40.00"
    assert updated_goal["is_achieved"] is False


def test_goal_marked_achieved_when_target_reached(client):
    token = _register_and_login(client, "goalachieved@example.com")
    account_id = _create_account(client, token)
    category_id = _create_category(client, token)
    goal = client.post(
        "/goals", json={"name": "Emergencia", "target_amount": "300.00"}, headers=_auth_headers(token)
    ).json()

    client.post(
        f"/goals/{goal['id']}/contributions",
        json={
            "account_id": account_id,
            "category_id": category_id,
            "type": "expense",
            "amount": "300.00",
            "occurred_at": "2026-09-10",
        },
        headers=_auth_headers(token),
    )

    updated_goal = client.get(f"/goals/{goal['id']}", headers=_auth_headers(token)).json()
    assert updated_goal["is_achieved"] is True


def test_cannot_contribute_to_another_users_goal(client):
    token_a = _register_and_login(client, "goalcontriba@example.com")
    token_b = _register_and_login(client, "goalcontribb@example.com")
    account_id = _create_account(client, token_b)
    category_id = _create_category(client, token_b)
    goal = client.post(
        "/goals", json={"name": "Meta A", "target_amount": "500.00"}, headers=_auth_headers(token_a)
    ).json()

    response = client.post(
        f"/goals/{goal['id']}/contributions",
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


def test_update_and_delete_goal(client):
    token = _register_and_login(client, "goalupdate@example.com")
    goal = client.post(
        "/goals", json={"name": "Antiga", "target_amount": "100.00"}, headers=_auth_headers(token)
    ).json()

    updated = client.patch(
        f"/goals/{goal['id']}", json={"name": "Nova"}, headers=_auth_headers(token)
    )
    deleted = client.delete(f"/goals/{goal['id']}", headers=_auth_headers(token))
    get_after_delete = client.get(f"/goals/{goal['id']}", headers=_auth_headers(token))

    assert updated.status_code == 200
    assert updated.json()["name"] == "Nova"
    assert deleted.status_code == 204
    assert get_after_delete.status_code == 404
