"""Marco 8 (RF-014 a RF-021): contas a pagar e a receber."""

from datetime import date, timedelta
from decimal import Decimal

import pytest

from src.features.commitments.service import add_months, split_amount

TODAY = date.today()


def _register_and_login(client, email: str) -> dict[str, str]:
    payload = {"email": email, "password": "supersecret1"}
    client.post("/auth/register", json=payload)
    token = client.post("/auth/login", json=payload).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _account(client, headers, name: str = "Corrente") -> str:
    return client.post("/accounts", json={"name": name, "type": "checking"}, headers=headers).json()["id"]


def _category(client, headers, name: str = "Moradia") -> str:
    return client.post("/categories", json={"name": name}, headers=headers).json()["id"]


def _setup(client, email: str):
    headers = _register_and_login(client, email)
    return headers, _account(client, headers), _category(client, headers)


def _create(client, headers, category_id, **overrides):
    body = {
        "direction": "payable",
        "description": "Aluguel",
        "amount": "100.00",
        "due_date": (TODAY + timedelta(days=10)).isoformat(),
        "category_id": category_id,
    }
    body.update(overrides)
    return client.post("/commitments", json=body, headers=headers)


def _one(client, headers, category_id, **overrides) -> dict:
    response = _create(client, headers, category_id, **overrides)
    assert response.status_code == 201, response.text
    return response.json()[0]


def _settle(client, headers, commitment_id, **body):
    return client.post(f"/commitments/{commitment_id}/settlements", json=body, headers=headers)


def _transactions(client, headers) -> list[dict]:
    return client.get("/transactions", headers=headers).json()


# ---------- funções puras ----------

def test_split_amount_keeps_total_and_gives_leftover_cents_to_first():
    parts = split_amount(Decimal("100.00"), 3)

    assert parts == [Decimal("33.34"), Decimal("33.33"), Decimal("33.33")]
    assert sum(parts) == Decimal("100.00")


@pytest.mark.parametrize(("total", "count"), [("0.05", 3), ("1000.00", 7), ("99.99", 12), ("10.00", 1)])
def test_split_amount_always_sums_to_total(total, count):
    assert sum(split_amount(Decimal(total), count)) == Decimal(total)


def test_add_months_clamps_to_shorter_months():
    assert add_months(date(2026, 1, 31), 1) == date(2026, 2, 28)
    assert add_months(date(2028, 1, 31), 1) == date(2028, 2, 29)
    assert add_months(date(2026, 11, 15), 3) == date(2027, 2, 15)


# ---------- criação e situação derivada ----------

def test_create_commitment_starts_open_with_full_balance(client):
    headers, _, category_id = _setup(client, "c1@example.com")

    item = _one(client, headers, category_id)

    assert item["status"] == "open"
    assert item["balance"] == "100.00"
    assert item["paid_amount"] == "0.00"
    assert item["installment_number"] is None


def test_status_is_derived_from_due_date(client):
    headers, _, category_id = _setup(client, "c2@example.com")

    overdue = _one(client, headers, category_id, due_date=(TODAY - timedelta(days=1)).isoformat())
    due_today = _one(client, headers, category_id, due_date=TODAY.isoformat())
    future = _one(client, headers, category_id)

    assert [overdue["status"], due_today["status"], future["status"]] == ["overdue", "due_today", "open"]


def test_installments_split_total_and_space_due_dates_monthly(client):
    headers, _, category_id = _setup(client, "c3@example.com")

    response = _create(client, headers, category_id, due_date="2026-01-31", installments=3)

    items = response.json()
    assert response.status_code == 201
    assert [i["amount"] for i in items] == ["33.34", "33.33", "33.33"]
    assert [i["due_date"] for i in items] == ["2026-01-31", "2026-02-28", "2026-03-31"]
    assert [(i["installment_number"], i["installment_count"]) for i in items] == [(1, 3), (2, 3), (3, 3)]
    assert len({i["installment_group_id"] for i in items}) == 1


def test_installments_are_settled_independently(client):
    headers, account_id, category_id = _setup(client, "c4@example.com")
    first, second = _create(client, headers, category_id, installments=2, account_id=account_id).json()

    _settle(client, headers, first["id"])

    listing = client.get("/commitments", headers=headers).json()["items"]
    assert {i["id"]: i["status"] for i in listing} == {first["id"]: "paid", second["id"]: "open"}
    assert _transactions(client, headers)[0]["description"] == "Aluguel (1/2)"


def test_create_validates_input(client):
    headers, _, category_id = _setup(client, "c5@example.com")

    assert _create(client, headers, category_id, amount="0").status_code == 422
    assert _create(client, headers, category_id, installments=0).status_code == 422
    assert _create(client, headers, category_id, installments=121).status_code == 422
    assert _create(client, headers, category_id, description="").status_code == 422
    assert _create(client, headers, category_id, direction="outro").status_code == 422


# ---------- baixa (RF-016, RF-017) ----------

def test_full_settlement_creates_one_expense_transaction(client):
    headers, account_id, category_id = _setup(client, "c6@example.com")
    item = _one(client, headers, category_id)
    paid_at = (TODAY - timedelta(days=2)).isoformat()

    response = _settle(client, headers, item["id"], account_id=account_id, paid_at=paid_at)

    body = response.json()
    assert response.status_code == 201
    assert body["status"] == "paid"
    assert body["balance"] == "0.00"
    assert len(body["settlements"]) == 1
    transactions = _transactions(client, headers)
    assert len(transactions) == 1
    assert (transactions[0]["type"], transactions[0]["amount"], transactions[0]["occurred_at"]) == ("expense", "100.00", paid_at)
    assert transactions[0]["category_id"] == category_id
    assert transactions[0]["id"] == body["settlements"][0]["transaction_id"]


def test_receivable_settlement_creates_income(client):
    headers, account_id, category_id = _setup(client, "c7@example.com")
    item = _one(client, headers, category_id, direction="receivable", description="Freela")

    _settle(client, headers, item["id"], account_id=account_id)

    assert _transactions(client, headers)[0]["type"] == "income"


def test_partial_settlements_keep_balance_open_until_paid(client):
    headers, account_id, category_id = _setup(client, "c8@example.com")
    item = _one(client, headers, category_id)

    first = _settle(client, headers, item["id"], amount="40.00", account_id=account_id).json()
    second = _settle(client, headers, item["id"], amount="60.00", account_id=account_id).json()

    assert (first["status"], first["balance"], first["paid_amount"]) == ("partially_paid", "60.00", "40.00")
    assert (second["status"], second["balance"]) == ("paid", "0.00")
    assert [t["amount"] for t in _transactions(client, headers)] == ["40.00", "60.00"]


def test_overdue_stays_overdue_after_partial_payment(client):
    headers, account_id, category_id = _setup(client, "c9@example.com")
    item = _one(client, headers, category_id, due_date=(TODAY - timedelta(days=3)).isoformat())

    body = _settle(client, headers, item["id"], amount="10.00", account_id=account_id).json()

    assert body["status"] == "overdue"
    assert body["balance"] == "90.00"


def test_settlement_above_balance_is_rejected_and_creates_nothing(client):
    headers, account_id, category_id = _setup(client, "c10@example.com")
    item = _one(client, headers, category_id)
    _settle(client, headers, item["id"], amount="70.00", account_id=account_id)

    response = _settle(client, headers, item["id"], amount="40.00", account_id=account_id)

    assert response.status_code == 422
    assert len(_transactions(client, headers)) == 1


def test_cannot_settle_paid_or_canceled_commitment(client):
    headers, account_id, category_id = _setup(client, "c11@example.com")
    paid = _one(client, headers, category_id)
    _settle(client, headers, paid["id"], account_id=account_id)
    canceled = _one(client, headers, category_id)
    client.post(f"/commitments/{canceled['id']}/cancel", headers=headers)

    assert _settle(client, headers, paid["id"], account_id=account_id).status_code == 409
    assert _settle(client, headers, canceled["id"], account_id=account_id).status_code == 409
    assert len(_transactions(client, headers)) == 1


def test_future_payment_date_is_rejected(client):
    headers, account_id, category_id = _setup(client, "c12@example.com")
    item = _one(client, headers, category_id)

    response = _settle(
        client, headers, item["id"], account_id=account_id, paid_at=(TODAY + timedelta(days=1)).isoformat()
    )

    assert response.status_code == 422
    assert _transactions(client, headers) == []


def test_settlement_uses_planned_account_and_requires_one(client):
    headers, account_id, category_id = _setup(client, "c13@example.com")
    planned = _one(client, headers, category_id, account_id=account_id)
    unplanned = _one(client, headers, category_id)

    ok = _settle(client, headers, planned["id"])
    missing = _settle(client, headers, unplanned["id"])

    assert ok.status_code == 201
    assert _transactions(client, headers)[0]["account_id"] == account_id
    assert missing.status_code == 422


def test_settlement_in_archived_account_is_rejected(client):
    headers, account_id, category_id = _setup(client, "c14@example.com")
    item = _one(client, headers, category_id)
    client.post(f"/accounts/{account_id}/archive", headers=headers)

    response = _settle(client, headers, item["id"], account_id=account_id)

    assert response.status_code == 422
    assert _transactions(client, headers) == []


def test_creating_with_archived_planned_account_is_rejected(client):
    headers, account_id, category_id = _setup(client, "c15@example.com")
    client.post(f"/accounts/{account_id}/archive", headers=headers)

    assert _create(client, headers, category_id, account_id=account_id).status_code == 422


# ---------- desfazer baixa (decisão 8) ----------

def test_undo_settlement_removes_payment_and_its_transaction(client):
    headers, account_id, category_id = _setup(client, "c16@example.com")
    item = _one(client, headers, category_id)
    settled = _settle(client, headers, item["id"], account_id=account_id).json()
    settlement_id = settled["settlements"][0]["id"]

    response = client.delete(f"/commitments/{item['id']}/settlements/{settlement_id}", headers=headers)

    assert response.status_code == 200
    assert response.json()["status"] == "open"
    assert response.json()["settlements"] == []
    assert _transactions(client, headers) == []


def test_undo_only_removes_the_chosen_settlement(client):
    headers, account_id, category_id = _setup(client, "c17@example.com")
    item = _one(client, headers, category_id)
    _settle(client, headers, item["id"], amount="30.00", account_id=account_id)
    second = _settle(client, headers, item["id"], amount="20.00", account_id=account_id).json()
    chosen = next(s for s in second["settlements"] if s["amount"] == "20.00")

    body = client.delete(f"/commitments/{item['id']}/settlements/{chosen['id']}", headers=headers).json()

    assert (body["paid_amount"], body["balance"]) == ("30.00", "70.00")
    assert [t["amount"] for t in _transactions(client, headers)] == ["30.00"]


def test_undo_twice_returns_404(client):
    headers, account_id, category_id = _setup(client, "c18@example.com")
    item = _one(client, headers, category_id)
    settlement_id = _settle(client, headers, item["id"], account_id=account_id).json()["settlements"][0]["id"]
    client.delete(f"/commitments/{item['id']}/settlements/{settlement_id}", headers=headers)

    response = client.delete(f"/commitments/{item['id']}/settlements/{settlement_id}", headers=headers)

    assert response.status_code == 404


def test_manual_transactions_are_never_touched_by_undo(client):
    headers, account_id, category_id = _setup(client, "c19@example.com")
    client.post(
        "/transactions",
        headers=headers,
        json={"account_id": account_id, "category_id": category_id, "type": "expense", "amount": "5.00", "occurred_at": TODAY.isoformat()},
    )
    item = _one(client, headers, category_id)
    settlement_id = _settle(client, headers, item["id"], account_id=account_id).json()["settlements"][0]["id"]

    client.delete(f"/commitments/{item['id']}/settlements/{settlement_id}", headers=headers)

    assert [t["amount"] for t in _transactions(client, headers)] == ["5.00"]


# ---------- cancelar e editar (RF-020, RB-013) ----------

def test_cancel_removes_commitment_from_open_totals(client):
    headers, _, category_id = _setup(client, "c20@example.com")
    keep = _one(client, headers, category_id, amount="50.00")
    drop = _one(client, headers, category_id, amount="70.00")

    canceled = client.post(f"/commitments/{drop['id']}/cancel", headers=headers).json()
    listing = client.get("/commitments", headers=headers).json()

    assert canceled["status"] == "canceled"
    assert listing["totals"]["payable_balance"] == "50.00"
    assert {i["id"] for i in listing["items"]} == {keep["id"], drop["id"]}


def test_cancel_paid_or_already_canceled_is_rejected(client):
    headers, account_id, category_id = _setup(client, "c21@example.com")
    paid = _one(client, headers, category_id)
    _settle(client, headers, paid["id"], account_id=account_id)
    twice = _one(client, headers, category_id)
    client.post(f"/commitments/{twice['id']}/cancel", headers=headers)

    assert client.post(f"/commitments/{paid['id']}/cancel", headers=headers).status_code == 409
    assert client.post(f"/commitments/{twice['id']}/cancel", headers=headers).status_code == 409


def test_cancel_keeps_partial_payment_history(client):
    headers, account_id, category_id = _setup(client, "c22@example.com")
    item = _one(client, headers, category_id)
    _settle(client, headers, item["id"], amount="30.00", account_id=account_id)

    canceled = client.post(f"/commitments/{item['id']}/cancel", headers=headers).json()

    assert canceled["status"] == "canceled"
    assert canceled["paid_amount"] == "30.00"
    assert len(_transactions(client, headers)) == 1


def test_update_allows_free_fields_but_locks_amount_and_due_date_once_paid(client):
    headers, account_id, category_id = _setup(client, "c23@example.com")
    item = _one(client, headers, category_id)

    renamed = client.patch(f"/commitments/{item['id']}", json={"description": "Aluguel de outubro"}, headers=headers)
    _settle(client, headers, item["id"], account_id=account_id)
    locked = client.patch(f"/commitments/{item['id']}", json={"amount": "120.00"}, headers=headers)
    still_free = client.patch(f"/commitments/{item['id']}", json={"notes": "pago"}, headers=headers)

    assert renamed.json()["description"] == "Aluguel de outubro"
    assert locked.status_code == 409
    assert still_free.status_code == 200


def test_update_amount_cannot_go_below_what_was_paid(client):
    headers, account_id, category_id = _setup(client, "c24@example.com")
    item = _one(client, headers, category_id)
    _settle(client, headers, item["id"], amount="60.00", account_id=account_id)

    below = client.patch(f"/commitments/{item['id']}", json={"amount": "50.00"}, headers=headers)
    above = client.patch(f"/commitments/{item['id']}", json={"amount": "150.00"}, headers=headers)

    assert below.status_code == 422
    assert (above.json()["amount"], above.json()["balance"]) == ("150.00", "90.00")


def test_update_cannot_clear_required_fields_but_can_clear_optional_ones(client):
    headers, account_id, category_id = _setup(client, "c25@example.com")
    item = _one(client, headers, category_id, account_id=account_id, notes="x", counterparty="Imobiliária")

    assert client.patch(f"/commitments/{item['id']}", json={"category_id": None}, headers=headers).status_code == 422
    assert client.patch(f"/commitments/{item['id']}", json={"due_date": None}, headers=headers).status_code == 422
    cleared = client.patch(
        f"/commitments/{item['id']}", json={"account_id": None, "notes": None, "counterparty": None}, headers=headers
    ).json()
    assert (cleared["account_id"], cleared["notes"], cleared["counterparty"]) == (None, None, None)


# ---------- listagem, filtros e resumo (RF-019, RF-021) ----------

def test_list_filters_and_totals(client):
    headers, account_id, category_id = _setup(client, "c26@example.com")
    other_category = _category(client, headers, "Mercado")
    _one(client, headers, category_id, description="Aluguel", amount="1000.00", due_date=(TODAY - timedelta(days=5)).isoformat())
    _one(client, headers, other_category, description="Mercado", amount="200.00", due_date=(TODAY + timedelta(days=3)).isoformat())
    _one(client, headers, category_id, direction="receivable", description="Freela", amount="500.00", due_date=(TODAY + timedelta(days=20)).isoformat())
    paid = _one(client, headers, category_id, description="Internet", amount="100.00")
    _settle(client, headers, paid["id"], account_id=account_id)

    def names(**params):
        body = client.get("/commitments", params=params, headers=headers).json()
        return sorted(i["description"] for i in body["items"]), body["totals"]

    assert names(direction="receivable")[0] == ["Freela"]
    assert names(status="overdue")[0] == ["Aluguel"]
    assert names(status="paid")[0] == ["Internet"]
    assert names(status="pending")[0] == ["Aluguel", "Freela", "Mercado"]
    assert names(category_id=other_category)[0] == ["Mercado"]
    assert names(due_from=TODAY.isoformat(), due_to=(TODAY + timedelta(days=5)).isoformat())[0] == ["Mercado"]
    _, totals = names()
    assert (totals["payable_balance"], totals["receivable_balance"], totals["count"]) == ("1200.00", "500.00", 4)


def test_list_rejects_unknown_status(client):
    headers, _, _ = _setup(client, "c27@example.com")

    assert client.get("/commitments", params={"status": "qualquer"}, headers=headers).status_code == 422


def test_summary_counts_overdue_and_due_soon(client):
    headers, account_id, category_id = _setup(client, "c28@example.com")
    _one(client, headers, category_id, amount="300.00", due_date=(TODAY - timedelta(days=2)).isoformat())
    _one(client, headers, category_id, amount="50.00", due_date=(TODAY + timedelta(days=3)).isoformat())
    _one(client, headers, category_id, amount="999.00", due_date=(TODAY + timedelta(days=30)).isoformat())
    _one(client, headers, category_id, direction="receivable", amount="80.00", due_date=(TODAY - timedelta(days=1)).isoformat())
    settled = _one(client, headers, category_id, amount="10.00", due_date=(TODAY - timedelta(days=9)).isoformat())
    _settle(client, headers, settled["id"], account_id=account_id)

    body = client.get("/commitments/summary", headers=headers).json()

    assert body["days"] == 7
    assert (body["payable"]["overdue_count"], body["payable"]["overdue_amount"]) == (1, "300.00")
    assert (body["payable"]["due_soon_count"], body["payable"]["due_soon_amount"]) == (1, "50.00")
    assert body["payable"]["open_amount"] == "1349.00"
    assert (body["receivable"]["overdue_count"], body["receivable"]["overdue_amount"]) == (1, "80.00")


# ---------- isolamento e autenticação (RNF-001) ----------

def test_user_cannot_see_or_touch_another_users_commitment(client):
    owner, owner_account, owner_category = _setup(client, "c29owner@example.com")
    intruder, intruder_account, _ = _setup(client, "c29intruder@example.com")
    item = _one(client, owner, owner_category)
    settled = _one(client, owner, owner_category)
    settlement_id = _settle(client, owner, settled["id"], account_id=owner_account).json()["settlements"][0]["id"]

    assert client.get(f"/commitments/{item['id']}", headers=intruder).status_code == 404
    assert client.patch(f"/commitments/{item['id']}", json={"description": "x"}, headers=intruder).status_code == 404
    assert client.post(f"/commitments/{item['id']}/cancel", headers=intruder).status_code == 404
    assert _settle(client, intruder, item["id"], account_id=intruder_account).status_code == 404
    assert client.delete(f"/commitments/{settled['id']}/settlements/{settlement_id}", headers=intruder).status_code == 404
    assert client.get("/commitments", headers=intruder).json()["items"] == []
    assert client.get("/commitments/summary", headers=intruder).json()["payable"]["open_amount"] == "0.00"
    assert len(_transactions(client, owner)) == 1


def test_cannot_use_another_users_category_or_account(client):
    owner, owner_account, owner_category = _setup(client, "c30owner@example.com")
    intruder, intruder_account, intruder_category = _setup(client, "c30intruder@example.com")
    mine = _one(client, intruder, intruder_category)

    assert _create(client, intruder, owner_category).status_code == 404
    assert _create(client, intruder, intruder_category, account_id=owner_account).status_code == 404
    assert _settle(client, intruder, mine["id"], account_id=owner_account).status_code == 404
    assert client.patch(f"/commitments/{mine['id']}", json={"category_id": owner_category}, headers=intruder).status_code == 404
    assert _transactions(client, owner) == []


def test_requires_authentication(client):
    assert client.get("/commitments").status_code == 401
    assert client.get("/commitments/summary").status_code == 401
    assert client.post("/commitments", json={}).status_code == 401
