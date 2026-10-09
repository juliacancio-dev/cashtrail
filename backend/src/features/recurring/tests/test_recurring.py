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


# ---------- Marco 8, etapa 6 (RF-022): recorrência gerando conta a pagar/receber ----------

def _recurring(client, token, account_id, category_id, **overrides):
    body = {
        "account_id": account_id,
        "category_id": category_id,
        "type": "expense",
        "amount": "1200.00",
        "frequency": "monthly",
        "next_occurrence_date": "2026-09-10",
        "generate_as_commitment": True,
    }
    body.update(overrides)
    response = client.post("/recurring", json=body, headers=_auth_headers(token))
    assert response.status_code == 201, response.text
    return response.json()


def _commitments(client, token) -> list[dict]:
    return client.get("/commitments", headers=_auth_headers(token)).json()["items"]


def test_generate_as_commitment_defaults_to_false_and_is_returned(client):
    token = _register_and_login(client, "reccm1@example.com")
    account_id = _create_account(client, token)
    category_id = _create_category(client, token)

    default = _recurring(client, token, account_id, category_id, generate_as_commitment=False)
    flagged = _recurring(client, token, account_id, category_id)

    assert default["generate_as_commitment"] is False
    assert flagged["generate_as_commitment"] is True


def test_commitment_mode_creates_payable_with_lookahead_and_no_transaction(client, db_session):
    token = _register_and_login(client, "reccm2@example.com")
    account_id = _create_account(client, token)
    category_id = _create_category(client, token, "Moradia")
    recurring = _recurring(client, token, account_id, category_id, description="Aluguel")

    generated = recurring_service.generate_due_commitments(db_session, as_of=date(2026, 9, 15))

    items = sorted(_commitments(client, token), key=lambda c: c["due_date"])
    assert generated == 2  # 10/09 e 10/10: o horizonte de 31 dias (16/10) alcança as duas
    assert [(c["due_date"], c["direction"], c["amount"]) for c in items] == [
        ("2026-09-10", "payable", "1200.00"),
        ("2026-10-10", "payable", "1200.00"),
    ]
    assert {c["recurring_transaction_id"] for c in items} == {recurring["id"]}
    assert items[0]["account_id"] == account_id
    assert client.get("/transactions", headers=_auth_headers(token)).json() == []
    updated = client.get(f"/recurring/{recurring['id']}", headers=_auth_headers(token)).json()
    assert updated["next_occurrence_date"] == "2026-11-10"


def test_commitment_mode_falls_back_to_category_name_and_maps_income_to_receivable(client, db_session):
    token = _register_and_login(client, "reccm3@example.com")
    account_id = _create_account(client, token)
    category_id = _create_category(client, token, "Aluguel recebido")
    _recurring(client, token, account_id, category_id, type="income", amount="900.00")

    recurring_service.generate_due_commitments(db_session, as_of=date(2026, 9, 15))

    first = sorted(_commitments(client, token), key=lambda c: c["due_date"])[0]
    assert (first["direction"], first["description"]) == ("receivable", "Aluguel recebido")


def test_commitment_job_is_idempotent_even_if_the_date_was_not_advanced(client, db_session):
    """Simula o job que caiu entre criar o compromisso e avançar a data: não pode duplicar."""
    from src.features.recurring.models import RecurringTransaction

    token = _register_and_login(client, "reccm4@example.com")
    account_id = _create_account(client, token)
    category_id = _create_category(client, token)
    recurring = _recurring(client, token, account_id, category_id)
    recurring_service.generate_due_commitments(db_session, as_of=date(2026, 9, 15))
    assert len(_commitments(client, token)) == 2

    row = db_session.get(RecurringTransaction, recurring["id"])
    row.next_occurrence_date = date(2026, 9, 10)
    db_session.commit()
    generated = recurring_service.generate_due_commitments(db_session, as_of=date(2026, 9, 15))

    assert generated == 0
    assert len(_commitments(client, token)) == 2
    assert client.get(f"/recurring/{recurring['id']}", headers=_auth_headers(token)).json()["next_occurrence_date"] == "2026-11-10"


def test_weekly_commitment_mode_generates_each_week_inside_the_horizon(client, db_session):
    token = _register_and_login(client, "reccm5@example.com")
    account_id = _create_account(client, token)
    category_id = _create_category(client, token)
    recurring = _recurring(client, token, account_id, category_id, frequency="weekly", amount="50.00")

    generated = recurring_service.generate_due_commitments(db_session, as_of=date(2026, 9, 10))

    assert generated == 5  # 10/09, 17/09, 24/09, 01/10, 08/10 (horizonte 11/10)
    assert client.get(f"/recurring/{recurring['id']}", headers=_auth_headers(token)).json()["next_occurrence_date"] == "2026-10-15"


def test_commitment_job_caps_how_many_it_creates_per_run(client, db_session):
    token = _register_and_login(client, "reccm6@example.com")
    account_id = _create_account(client, token)
    category_id = _create_category(client, token)
    _recurring(client, token, account_id, category_id, frequency="weekly", next_occurrence_date="2025-01-01")

    generated = recurring_service.generate_due_commitments(db_session, as_of=date(2026, 9, 10))

    assert generated == recurring_service.MAX_COMMITMENTS_PER_RUN


def test_commitment_job_skips_and_retries_when_account_became_archived(client, db_session):
    token = _register_and_login(client, "reccm7@example.com")
    account_id = _create_account(client, token)
    category_id = _create_category(client, token)
    recurring = _recurring(client, token, account_id, category_id)
    client.post(f"/accounts/{account_id}/archive", headers=_auth_headers(token))

    generated = recurring_service.generate_due_commitments(db_session, as_of=date(2026, 9, 15))

    assert generated == 0
    assert _commitments(client, token) == []
    assert client.get(f"/recurring/{recurring['id']}", headers=_auth_headers(token)).json()["next_occurrence_date"] == "2026-09-10"


def test_each_job_only_handles_its_own_mode(client, db_session):
    token = _register_and_login(client, "reccm8@example.com")
    account_id = _create_account(client, token)
    category_id = _create_category(client, token)
    _recurring(client, token, account_id, category_id, generate_as_commitment=False, description="Streaming")
    _recurring(client, token, account_id, category_id, generate_as_commitment=True, description="Aluguel")

    transactions = recurring_service.generate_due_transactions(db_session, as_of=date(2026, 9, 15))
    commitments = recurring_service.generate_due_commitments(db_session, as_of=date(2026, 9, 15))

    assert (transactions, commitments) == (1, 2)
    assert [t["description"] for t in client.get("/transactions", headers=_auth_headers(token)).json()] == ["Streaming"]
    assert {c["description"] for c in _commitments(client, token)} == {"Aluguel"}


def test_inactive_commitment_recurrence_stops_generating(client, db_session):
    token = _register_and_login(client, "reccm9@example.com")
    account_id = _create_account(client, token)
    category_id = _create_category(client, token)
    recurring = _recurring(client, token, account_id, category_id)
    client.post(f"/recurring/{recurring['id']}/deactivate", headers=_auth_headers(token))

    assert recurring_service.generate_due_commitments(db_session, as_of=date(2026, 9, 15)) == 0


def test_generated_commitment_can_be_paid_and_becomes_a_transaction(client, db_session):
    token = _register_and_login(client, "reccm10@example.com")
    account_id = _create_account(client, token)
    category_id = _create_category(client, token)
    _recurring(client, token, account_id, category_id, description="Aluguel")
    recurring_service.generate_due_commitments(db_session, as_of=date(2026, 9, 15))
    first = sorted(_commitments(client, token), key=lambda c: c["due_date"])[0]

    response = client.post(
        f"/commitments/{first['id']}/settlements",
        json={"amount": "1200.00", "paid_at": "2026-09-10"},
        headers=_auth_headers(token),
    )

    assert response.status_code == 201
    transactions = client.get("/transactions", headers=_auth_headers(token)).json()
    assert [(t["type"], t["amount"], t["occurred_at"]) for t in transactions] == [("expense", "1200.00", "2026-09-10")]
