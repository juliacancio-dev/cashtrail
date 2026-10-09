"""Marco 9 (RF-023, RB-014, RB-015): transferência entre contas."""

from datetime import date, timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from src.features.transfers.models import Transfer

TODAY = date.today()


def _register_and_login(client, email: str) -> dict[str, str]:
    payload = {"email": email, "password": "supersecret1"}
    client.post("/auth/register", json=payload)
    token = client.post("/auth/login", json=payload).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _account(client, headers, name: str, type_: str = "checking") -> str:
    return client.post("/accounts", json={"name": name, "type": type_}, headers=headers).json()["id"]


def _setup(client, email: str):
    headers = _register_and_login(client, email)
    return headers, _account(client, headers, "Corrente"), _account(client, headers, "Cartão", "credit_card")


def _transfer(client, headers, from_id, to_id, **overrides):
    body = {"from_account_id": from_id, "to_account_id": to_id, "amount": "250.00", "occurred_at": TODAY.isoformat()}
    body.update(overrides)
    return client.post("/transfers", json=body, headers=headers)


def test_create_and_get_transfer(client):
    headers, checking, card = _setup(client, "t1@example.com")

    response = _transfer(client, headers, checking, card, description="Pagamento da fatura")

    body = response.json()
    assert response.status_code == 201
    assert (body["from_account_id"], body["to_account_id"], body["amount"]) == (checking, card, "250.00")
    assert body["description"] == "Pagamento da fatura"
    assert client.get(f"/transfers/{body['id']}", headers=headers).json()["id"] == body["id"]


def test_list_filters_by_period_and_account(client):
    headers, checking, card = _setup(client, "t2@example.com")
    savings = _account(client, headers, "Poupança", "savings")
    old = _transfer(client, headers, checking, card, occurred_at=(TODAY - timedelta(days=40)).isoformat()).json()
    recent = _transfer(client, headers, checking, savings).json()
    other = _transfer(client, headers, savings, card, amount="10.00").json()

    def ids(**params):
        return {t["id"] for t in client.get("/transfers", params=params, headers=headers).json()}

    assert ids() == {old["id"], recent["id"], other["id"]}
    assert ids(start_date=(TODAY - timedelta(days=5)).isoformat()) == {recent["id"], other["id"]}
    assert ids(account_id=card) == {old["id"], other["id"]}  # a conta pode ser origem ou destino
    assert ids(account_id=savings) == {recent["id"], other["id"]}


def test_delete_transfer(client):
    headers, checking, card = _setup(client, "t3@example.com")
    created = _transfer(client, headers, checking, card).json()

    deleted = client.delete(f"/transfers/{created['id']}", headers=headers)

    assert deleted.status_code == 204
    assert client.get("/transfers", headers=headers).json() == []
    assert client.delete(f"/transfers/{created['id']}", headers=headers).status_code == 404


def test_same_account_is_rejected(client):
    headers, checking, _ = _setup(client, "t4@example.com")

    assert _transfer(client, headers, checking, checking).status_code == 422
    assert client.get("/transfers", headers=headers).json() == []


def test_validates_amount_and_date(client):
    headers, checking, card = _setup(client, "t5@example.com")

    assert _transfer(client, headers, checking, card, amount="0").status_code == 422
    assert _transfer(client, headers, checking, card, amount="-5.00").status_code == 422
    assert _transfer(client, headers, checking, card, amount="10.005").status_code == 422
    future = _transfer(client, headers, checking, card, occurred_at=(TODAY + timedelta(days=1)).isoformat())
    assert future.status_code == 422
    assert client.get("/transfers", headers=headers).json() == []


def test_archived_account_is_rejected_on_either_side(client):
    headers, checking, card = _setup(client, "t6@example.com")
    client.post(f"/accounts/{card}/archive", headers=headers)

    assert _transfer(client, headers, checking, card).status_code == 422
    assert _transfer(client, headers, card, checking).status_code == 422


def test_unknown_account_returns_404(client):
    headers, checking, _ = _setup(client, "t7@example.com")

    assert _transfer(client, headers, checking, "00000000-0000-0000-0000-000000000000").status_code == 404


def test_transfer_does_not_change_dashboard_totals(client):
    """RB-014: transferência não é receita nem despesa."""
    headers, checking, card = _setup(client, "t8@example.com")
    category = client.post("/categories", json={"name": "Mercado"}, headers=headers).json()["id"]
    for kind, amount in (("income", "1000.00"), ("expense", "300.00")):
        client.post(
            "/transactions",
            headers=headers,
            json={"account_id": checking, "category_id": category, "type": kind, "amount": amount, "occurred_at": TODAY.isoformat()},
        )
    before = client.get("/dashboard", headers=headers).json()
    transactions_before = client.get("/transactions", headers=headers).json()

    assert _transfer(client, headers, checking, card, amount="500.00").status_code == 201

    after = client.get("/dashboard", headers=headers).json()
    assert after == before
    assert after["summary"]["income_total"] == "1000.00"
    assert after["summary"]["expense_total"] == "300.00"
    assert client.get("/transactions", headers=headers).json() == transactions_before


def test_database_rejects_same_account_and_non_positive_amount(client, db_session):
    """As regras também valem direto no banco, não só na API."""
    headers, checking, card = _setup(client, "t9@example.com")
    user_id = client.get("/auth/me", headers=headers).json()["id"]

    cases = {
        "ck_transfers_different_accounts": (checking, checking, 10),
        "ck_transfers_amount_positive (zero)": (checking, card, 0),
        "ck_transfers_amount_positive (negativo)": (checking, card, -1),
    }
    for name, (from_id, to_id, amount) in cases.items():
        # savepoint por tentativa: um rollback da sessão desfaria a transação inteira do teste
        # e as tentativas seguintes falhariam por FK ausente, não pela regra que queremos provar.
        with pytest.raises(IntegrityError) as raised:
            with db_session.begin_nested():
                db_session.add(
                    Transfer(user_id=user_id, from_account_id=from_id, to_account_id=to_id, amount=amount, occurred_at=TODAY)
                )
        assert "ck_transfers" in str(raised.value), f"{name}: falhou por outro motivo: {raised.value}"


def test_user_cannot_see_or_use_another_users_transfers_or_accounts(client):
    owner, owner_checking, owner_card = _setup(client, "t10owner@example.com")
    intruder, intruder_checking, _ = _setup(client, "t10intruder@example.com")
    mine = _transfer(client, owner, owner_checking, owner_card).json()

    assert client.get(f"/transfers/{mine['id']}", headers=intruder).status_code == 404
    assert client.delete(f"/transfers/{mine['id']}", headers=intruder).status_code == 404
    assert client.get("/transfers", headers=intruder).json() == []
    assert _transfer(client, intruder, intruder_checking, owner_card).status_code == 404
    assert _transfer(client, intruder, owner_checking, intruder_checking).status_code == 404
    assert len(client.get("/transfers", headers=owner).json()) == 1


def test_requires_authentication(client):
    assert client.get("/transfers").status_code == 401
    assert client.post("/transfers", json={}).status_code == 401
