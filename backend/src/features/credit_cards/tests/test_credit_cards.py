"""Marco 9 (RF-024 a RF-030): cartões de crédito e faturas.

Datas fixas no passado (março a maio de 2026) deixam as situações determinísticas: com
fechamento dia 5 e vencimento dia 12, essas faturas já venceram. Os testes de "a vencer"
e de "aberta" usam datas relativas a hoje.
"""

from datetime import date, timedelta

TODAY = date.today()
MARCH = "2026-03-05"   # fatura de 06/02 a 05/03, vence 12/03
APRIL = "2026-04-05"
MAY = "2026-05-05"


def _register_and_login(client, email: str) -> dict[str, str]:
    payload = {"email": email, "password": "supersecret1"}
    client.post("/auth/register", json=payload)
    token = client.post("/auth/login", json=payload).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _account(client, headers, name: str, type_: str = "checking") -> str:
    return client.post("/accounts", json={"name": name, "type": type_}, headers=headers).json()["id"]


def _setup(client, email: str, closing_day: int = 5, due_day: int = 12, limit: str | None = "1000.00"):
    headers = _register_and_login(client, email)
    checking = _account(client, headers, "Corrente")
    card_account = _account(client, headers, "Cartão", "credit_card")
    category = client.post("/categories", json={"name": "Compras"}, headers=headers).json()["id"]
    body = {
        "account_id": card_account,
        "closing_day": closing_day,
        "due_day": due_day,
        "default_payment_account_id": checking,
    }
    if limit:
        body["credit_limit"] = limit
    response = client.post("/cards", json=body, headers=headers)
    assert response.status_code == 201, response.text
    return headers, checking, card_account, category, response.json()["id"]


def _buy(client, headers, card_id, category, **overrides):
    body = {"description": "Notebook", "amount": "100.00", "purchase_date": "2026-03-03", "category_id": category}
    body.update(overrides)
    return client.post(f"/cards/{card_id}/purchases", json=body, headers=headers)


def _invoice(client, headers, card_id, closing) -> dict:
    return client.get(f"/cards/{card_id}/invoices/{closing}", headers=headers).json()


def _pay(client, headers, card_id, closing, **body):
    return client.post(f"/cards/{card_id}/invoices/{closing}/payments", json=body, headers=headers)


# ---------- cadastro do cartão (RF-024) ----------

def test_card_requires_a_credit_card_account_and_is_unique(client):
    headers, checking, card_account, _, _ = _setup(client, "cc1@example.com")

    on_checking = client.post("/cards", json={"account_id": checking, "closing_day": 5, "due_day": 12}, headers=headers)
    duplicate = client.post("/cards", json={"account_id": card_account, "closing_day": 5, "due_day": 12}, headers=headers)

    assert on_checking.status_code == 422
    assert duplicate.status_code == 409


def test_card_validates_input_and_accounts(client):
    headers = _register_and_login(client, "cc2@example.com")
    card_account = _account(client, headers, "Cartão", "credit_card")
    other_card = _account(client, headers, "Outro", "credit_card")

    def create(**overrides):
        body = {"account_id": card_account, "closing_day": 5, "due_day": 12}
        body.update(overrides)
        return client.post("/cards", json=body, headers=headers).status_code

    assert create(closing_day=0) == 422
    assert create(due_day=32) == 422
    assert create(credit_limit="0") == 422
    assert create(default_payment_account_id=card_account) == 422  # não pode pagar com ele mesmo
    assert create(account_id="00000000-0000-0000-0000-000000000000") == 404
    client.post(f"/accounts/{other_card}/archive", headers=headers)
    assert create(account_id=other_card) == 422


def test_card_shows_debt_available_and_over_limit(client):
    headers, _, _, category, card_id = _setup(client, "cc3@example.com", limit="1000.00")

    empty = client.get(f"/cards/{card_id}", headers=headers).json()
    _buy(client, headers, card_id, category, amount="300.00")
    used = client.get(f"/cards/{card_id}", headers=headers).json()
    _buy(client, headers, card_id, category, amount="800.00")
    over = client.get(f"/cards/{card_id}", headers=headers).json()

    assert (empty["debt"], empty["available"], empty["over_limit"]) == ("0.00", "1000.00", False)
    assert (used["debt"], used["available"], used["over_limit"]) == ("300.00", "700.00", False)
    assert (over["debt"], over["available"], over["over_limit"]) == ("1100.00", "-100.00", True)


def test_card_debt_includes_the_opening_balance(client):
    """Saldo inicial negativo no cartão = dívida que já existia antes de usar o app."""
    headers, _, card_account, category, card_id = _setup(client, "cc3b@example.com", limit="1000.00")
    client.patch(f"/accounts/{card_account}", json={"opening_balance": "-400.00"}, headers=headers)

    before = client.get(f"/cards/{card_id}", headers=headers).json()
    _buy(client, headers, card_id, category, amount="100.00")
    after = client.get(f"/cards/{card_id}", headers=headers).json()

    assert (before["debt"], before["available"]) == ("400.00", "600.00")
    assert (after["debt"], after["available"]) == ("500.00", "500.00")


def test_card_without_limit_has_no_available(client):
    headers, _, _, _, card_id = _setup(client, "cc4@example.com", limit=None)

    card = client.get(f"/cards/{card_id}", headers=headers).json()

    assert (card["credit_limit"], card["available"], card["over_limit"]) == (None, None, False)


# ---------- compras e fatura (RF-025, RF-027, RB-019) ----------

def test_purchase_goes_to_the_first_invoice_that_closes_on_or_after_it(client):
    headers, _, _, category, card_id = _setup(client, "cc5@example.com")

    before = _buy(client, headers, card_id, category, purchase_date="2026-03-03").json()[0]
    on_closing = _buy(client, headers, card_id, category, purchase_date="2026-03-05").json()[0]
    after = _buy(client, headers, card_id, category, purchase_date="2026-03-06").json()[0]

    assert before["invoice_closing_date"] == MARCH
    assert on_closing["invoice_closing_date"] == MARCH   # RB-019: no dia do fechamento, inclusive
    assert after["invoice_closing_date"] == APRIL
    assert _invoice(client, headers, card_id, MARCH)["total"] == "200.00"
    assert _invoice(client, headers, card_id, APRIL)["total"] == "100.00"


def test_purchase_creates_exactly_one_expense_on_the_card_account(client):
    headers, _, card_account, category, card_id = _setup(client, "cc6@example.com")

    _buy(client, headers, card_id, category, amount="59.90")

    transactions = client.get("/transactions", headers=headers).json()
    assert [(t["account_id"], t["type"], t["amount"]) for t in transactions] == [(card_account, "expense", "59.90")]


def test_invoice_has_period_due_date_and_status(client):
    headers, _, _, category, card_id = _setup(client, "cc7@example.com")
    _buy(client, headers, card_id, category)

    invoice = _invoice(client, headers, card_id, MARCH)

    assert (invoice["period_start"], invoice["closing_date"], invoice["due_date"]) == ("2026-02-06", MARCH, "2026-03-12")
    assert (invoice["status"], invoice["balance"], invoice["purchases_count"]) == ("overdue", "100.00", 1)
    assert (invoice["previous_closing_date"], invoice["next_closing_date"]) == ("2026-02-05", APRIL)


def test_invoice_list_includes_current_cycle_even_when_empty_and_is_newest_first(client):
    headers, _, _, category, card_id = _setup(client, "cc8@example.com")
    _buy(client, headers, card_id, category, purchase_date="2026-03-03")
    _buy(client, headers, card_id, category, purchase_date="2026-04-03")

    invoices = client.get(f"/cards/{card_id}/invoices", headers=headers).json()

    closings = [i["closing_date"] for i in invoices]
    assert closings == sorted(closings, reverse=True)
    assert MARCH in closings and APRIL in closings
    assert len(closings) == 3  # as duas com compras + o ciclo de hoje, vazio
    assert {i["status"] for i in invoices if i["closing_date"] in (MARCH, APRIL)} == {"overdue"}


def test_current_cycle_is_open_and_a_future_one_is_future(client):
    headers, _, _, category, card_id = _setup(client, "cc9@example.com")
    _buy(client, headers, card_id, category, purchase_date=TODAY.isoformat(), installments=3)

    statuses = [i["status"] for i in client.get(f"/cards/{card_id}/invoices", headers=headers).json()]

    assert statuses[-1] == "open"          # o ciclo de hoje
    assert statuses[0] == "future"         # a 3ª parcela, dois ciclos à frente


def test_refund_on_the_card_account_reduces_the_invoice(client):
    headers, _, card_account, category, card_id = _setup(client, "cc10@example.com")
    _buy(client, headers, card_id, category, amount="100.00")

    client.post(
        "/transactions",
        headers=headers,
        json={"account_id": card_account, "category_id": category, "type": "income", "amount": "30.00", "occurred_at": "2026-03-04"},
    )

    assert _invoice(client, headers, card_id, MARCH)["total"] == "70.00"
    assert client.get(f"/cards/{card_id}", headers=headers).json()["debt"] == "70.00"


def test_legacy_expense_on_the_card_account_is_placed_by_date(client):
    headers, _, card_account, category, card_id = _setup(client, "cc11@example.com")
    client.post(
        "/transactions",
        headers=headers,
        json={"account_id": card_account, "category_id": category, "type": "expense", "amount": "80.00", "occurred_at": "2026-03-10"},
    )

    assert _invoice(client, headers, card_id, APRIL)["total"] == "80.00"


def test_invalid_closing_date_is_rejected(client):
    headers, _, _, category, card_id = _setup(client, "cc12@example.com")

    assert client.get(f"/cards/{card_id}/invoices/2026-04-06", headers=headers).status_code == 422
    assert _buy(client, headers, card_id, category, invoice_closing_date="2026-04-06").status_code == 422
    assert client.get("/transactions", headers=headers).json() == []


# ---------- parcelamento (RF-026) ----------

def test_installments_create_one_expense_per_invoice(client):
    headers, _, _, category, card_id = _setup(client, "cc13@example.com")

    entries = _buy(client, headers, card_id, category, amount="300.00", installments=3).json()

    assert [(e["amount"], e["occurred_at"], e["invoice_closing_date"]) for e in entries] == [
        ("100.00", "2026-03-03", MARCH),
        ("100.00", "2026-04-03", APRIL),
        ("100.00", "2026-05-03", MAY),
    ]
    assert [e["description"] for e in entries] == ["Notebook (1/3)", "Notebook (2/3)", "Notebook (3/3)"]
    assert [_invoice(client, headers, card_id, c)["total"] for c in (MARCH, APRIL, MAY)] == ["100.00"] * 3
    assert len(client.get("/transactions", headers=headers).json()) == 3
    assert client.get(f"/cards/{card_id}", headers=headers).json()["debt"] == "300.00"  # consome o limite todo


def test_installments_split_cents_with_leftover_on_first(client):
    headers, _, _, category, card_id = _setup(client, "cc14@example.com")

    entries = _buy(client, headers, card_id, category, amount="100.00", installments=3).json()

    assert [e["amount"] for e in entries] == ["33.34", "33.33", "33.33"]


def test_installments_can_start_on_a_chosen_invoice(client):
    headers, _, _, category, card_id = _setup(client, "cc15@example.com")

    entries = _buy(client, headers, card_id, category, amount="200.00", installments=2, invoice_closing_date=APRIL).json()

    assert [e["invoice_closing_date"] for e in entries] == [APRIL, MAY]
    assert entries[0]["moved"] is True  # a data da compra apontaria para março


def test_installments_limits(client):
    headers, _, _, category, card_id = _setup(client, "cc16@example.com")

    assert _buy(client, headers, card_id, category, installments=0).status_code == 422
    assert _buy(client, headers, card_id, category, installments=61).status_code == 422
    assert _buy(client, headers, card_id, category, amount="0").status_code == 422


def test_purchase_with_foreign_category_creates_nothing(client):
    headers, _, _, _, card_id = _setup(client, "cc17@example.com")
    other = _register_and_login(client, "cc17other@example.com")
    foreign_category = client.post("/categories", json={"name": "Alheia"}, headers=other).json()["id"]

    response = _buy(client, headers, card_id, foreign_category, installments=3)

    assert response.status_code == 404
    assert client.get("/transactions", headers=headers).json() == []


# ---------- mover compra (decisão 3) ----------

def test_move_purchase_to_another_invoice(client):
    headers, _, _, category, card_id = _setup(client, "cc18@example.com")
    entry = _buy(client, headers, card_id, category, purchase_date="2026-03-05").json()[0]

    moved = client.patch(
        f"/cards/{card_id}/purchases/{entry['transaction_id']}", json={"invoice_closing_date": APRIL}, headers=headers
    )

    assert moved.status_code == 200
    assert (moved.json()["invoice_closing_date"], moved.json()["moved"]) == (APRIL, True)
    assert _invoice(client, headers, card_id, MARCH)["total"] == "0.00"
    assert _invoice(client, headers, card_id, APRIL)["total"] == "100.00"


def test_move_works_for_a_legacy_expense_and_can_be_moved_back(client):
    headers, _, card_account, category, card_id = _setup(client, "cc19@example.com")
    legacy = client.post(
        "/transactions",
        headers=headers,
        json={"account_id": card_account, "category_id": category, "type": "expense", "amount": "50.00", "occurred_at": "2026-03-05"},
    ).json()

    client.patch(f"/cards/{card_id}/purchases/{legacy['id']}", json={"invoice_closing_date": APRIL}, headers=headers)
    back = client.patch(f"/cards/{card_id}/purchases/{legacy['id']}", json={"invoice_closing_date": MARCH}, headers=headers)

    assert (back.json()["invoice_closing_date"], back.json()["moved"]) == (MARCH, False)


def test_move_rejects_invalid_invoice_and_foreign_transactions(client):
    headers, checking, _, category, card_id = _setup(client, "cc20@example.com")
    entry = _buy(client, headers, card_id, category).json()[0]
    on_checking = client.post(
        "/transactions",
        headers=headers,
        json={"account_id": checking, "category_id": category, "type": "expense", "amount": "5.00", "occurred_at": "2026-03-03"},
    ).json()

    assert client.patch(f"/cards/{card_id}/purchases/{entry['transaction_id']}", json={"invoice_closing_date": "2026-04-06"}, headers=headers).status_code == 422
    assert client.patch(f"/cards/{card_id}/purchases/{on_checking['id']}", json={"invoice_closing_date": APRIL}, headers=headers).status_code == 404


# ---------- pagar a fatura (RF-028, RB-014, RB-016, RB-018) ----------

def test_paying_the_invoice_is_a_transfer_and_does_not_change_the_dashboard(client):
    headers, checking, card_account, category, card_id = _setup(client, "cc21@example.com")
    _buy(client, headers, card_id, category, amount="100.00")
    period = {"start_date": "2026-03-01", "end_date": "2026-03-31"}
    dashboard_before = client.get("/dashboard", params=period, headers=headers).json()
    transactions_before = client.get("/transactions", headers=headers).json()

    paid = _pay(client, headers, card_id, MARCH, paid_at="2026-03-10")

    assert paid.status_code == 201
    invoice = paid.json()
    assert (invoice["status"], invoice["balance"], invoice["paid"]) == ("paid", "0.00", "100.00")
    transfers = client.get("/transfers", headers=headers).json()
    assert [(t["from_account_id"], t["to_account_id"], t["amount"], t["occurred_at"]) for t in transfers] == [
        (checking, card_account, "100.00", "2026-03-10")
    ]
    assert client.get("/dashboard", params=period, headers=headers).json() == dashboard_before  # RB-016
    assert client.get("/transactions", headers=headers).json() == transactions_before         # nenhuma despesa nova
    card = client.get(f"/cards/{card_id}", headers=headers).json()
    assert (card["debt"], card["available"]) == ("0.00", "1000.00")


def test_partial_payments_keep_the_rest_on_the_same_invoice(client):
    headers, _, _, category, card_id = _setup(client, "cc22@example.com")
    _buy(client, headers, card_id, category, amount="100.00")

    first = _pay(client, headers, card_id, MARCH, amount="40.00", paid_at="2026-03-10").json()
    second = _pay(client, headers, card_id, MARCH, amount="60.00", paid_at="2026-03-11").json()

    assert (first["balance"], first["status"]) == ("60.00", "overdue")  # o resto continua vencido
    assert (second["balance"], second["status"]) == ("0.00", "paid")
    assert [p["amount"] for p in second["payments"]] == ["40.00", "60.00"]


def test_payment_above_balance_or_on_a_paid_invoice_is_rejected(client):
    headers, _, _, category, card_id = _setup(client, "cc23@example.com")
    _buy(client, headers, card_id, category, amount="100.00")

    above = _pay(client, headers, card_id, MARCH, amount="100.01", paid_at="2026-03-10")
    _pay(client, headers, card_id, MARCH, paid_at="2026-03-10")
    again = _pay(client, headers, card_id, MARCH, amount="1.00", paid_at="2026-03-10")

    assert above.status_code == 422   # RB-018
    assert again.status_code == 409
    assert len(client.get("/transfers", headers=headers).json()) == 1


def test_payment_needs_a_source_account_and_a_valid_one(client):
    headers, checking, card_account, category, card_id = _setup(client, "cc24@example.com")
    other_headers = _register_and_login(client, "cc24other@example.com")
    foreign_account = _account(client, other_headers, "Alheia")
    _buy(client, headers, card_id, category)
    client.patch(f"/cards/{card_id}", json={"default_payment_account_id": None}, headers=headers)
    savings = _account(client, headers, "Poupança", "savings")

    assert _pay(client, headers, card_id, MARCH, paid_at="2026-03-10").status_code == 422  # sem padrão e sem origem
    assert _pay(client, headers, card_id, MARCH, from_account_id=card_account, paid_at="2026-03-10").status_code == 422
    assert _pay(client, headers, card_id, MARCH, from_account_id=foreign_account, paid_at="2026-03-10").status_code == 404
    assert _pay(client, headers, card_id, MARCH, from_account_id=savings, paid_at="2026-03-10").status_code == 201
    assert client.get("/transfers", headers=headers).json()[0]["from_account_id"] == savings


def test_payment_with_archived_source_or_future_date_is_rejected(client):
    headers, checking, _, category, card_id = _setup(client, "cc25@example.com")
    _buy(client, headers, card_id, category)

    future = _pay(client, headers, card_id, MARCH, paid_at=(TODAY + timedelta(days=1)).isoformat())
    client.post(f"/accounts/{checking}/archive", headers=headers)
    archived = _pay(client, headers, card_id, MARCH, paid_at="2026-03-10")

    assert future.status_code == 422
    assert archived.status_code == 422
    assert client.get("/transfers", headers=headers).json() == []


def test_undo_payment_removes_link_and_transfer(client):
    headers, _, _, category, card_id = _setup(client, "cc26@example.com")
    _buy(client, headers, card_id, category, amount="100.00")
    payment_id = _pay(client, headers, card_id, MARCH, paid_at="2026-03-10").json()["payments"][0]["id"]

    undone = client.delete(f"/cards/{card_id}/invoices/{MARCH}/payments/{payment_id}", headers=headers)

    assert undone.status_code == 200
    assert (undone.json()["balance"], undone.json()["payments"]) == ("100.00", [])
    assert client.get("/transfers", headers=headers).json() == []
    assert client.get(f"/cards/{card_id}", headers=headers).json()["debt"] == "100.00"
    assert client.delete(f"/cards/{card_id}/invoices/{MARCH}/payments/{payment_id}", headers=headers).status_code == 404


def test_undo_payment_on_the_wrong_invoice_is_not_found(client):
    headers, _, _, category, card_id = _setup(client, "cc27@example.com")
    _buy(client, headers, card_id, category)
    payment_id = _pay(client, headers, card_id, MARCH, paid_at="2026-03-10").json()["payments"][0]["id"]

    wrong = client.delete(f"/cards/{card_id}/invoices/{APRIL}/payments/{payment_id}", headers=headers)

    assert wrong.status_code == 404
    assert len(client.get("/transfers", headers=headers).json()) == 1


# ---------- editar o cartão ----------

def test_changing_closing_day_keeps_each_invoice_in_the_same_month(client):
    headers, _, _, category, card_id = _setup(client, "cc28@example.com")
    entry = _buy(client, headers, card_id, category, purchase_date="2026-03-05").json()[0]
    client.patch(f"/cards/{card_id}/purchases/{entry['transaction_id']}", json={"invoice_closing_date": APRIL}, headers=headers)
    _pay(client, headers, card_id, APRIL, paid_at="2026-04-10", amount="40.00")

    updated = client.patch(f"/cards/{card_id}", json={"closing_day": 10}, headers=headers)

    assert updated.status_code == 200
    invoice = _invoice(client, headers, card_id, "2026-04-10")
    assert (invoice["total"], invoice["paid"], invoice["balance"]) == ("100.00", "40.00", "60.00")
    assert client.get(f"/cards/{card_id}/invoices/{APRIL}", headers=headers).status_code == 422  # 05/04 deixou de ser fechamento


def test_update_validates_and_can_clear_the_limit(client):
    headers, checking, card_account, _, card_id = _setup(client, "cc29@example.com")

    assert client.patch(f"/cards/{card_id}", json={"closing_day": None}, headers=headers).status_code == 422
    assert client.patch(f"/cards/{card_id}", json={"due_day": 40}, headers=headers).status_code == 422
    assert client.patch(f"/cards/{card_id}", json={"default_payment_account_id": card_account}, headers=headers).status_code == 422
    cleared = client.patch(f"/cards/{card_id}", json={"credit_limit": None}, headers=headers).json()
    assert (cleared["credit_limit"], cleared["available"]) == (None, None)


# ---------- resumo para o alerta (RF-030) ----------

def test_summary_counts_overdue_and_due_soon_invoices(client):
    headers, _, _, category, card_id = _setup(client, "cc30@example.com")
    _buy(client, headers, card_id, category, amount="100.00")  # março: já vencida

    # Segundo cartão com fatura que fechou há 2 dias e vence em 3.
    closing = TODAY - timedelta(days=2)
    soon_account = _account(client, headers, "Cartão 2", "credit_card")
    soon = client.post(
        "/cards",
        json={"account_id": soon_account, "closing_day": closing.day, "due_day": (TODAY + timedelta(days=3)).day},
        headers=headers,
    ).json()["id"]
    _buy(client, headers, soon, category, amount="200.00", purchase_date=closing.isoformat())

    body = client.get("/cards/summary", headers=headers).json()

    assert (body["overdue_count"], body["overdue_amount"]) == (1, "100.00")
    assert (body["due_soon_count"], body["due_soon_amount"]) == (1, "200.00")
    assert body["debt"] == "300.00"


def test_summary_ignores_open_invoices_and_paid_ones(client):
    headers, _, _, category, card_id = _setup(client, "cc31@example.com")
    _buy(client, headers, card_id, category, purchase_date=TODAY.isoformat())  # fatura aberta
    _buy(client, headers, card_id, category, amount="50.00")
    _pay(client, headers, card_id, MARCH, paid_at="2026-03-10")

    body = client.get("/cards/summary", headers=headers).json()

    assert (body["overdue_count"], body["due_soon_count"]) == (0, 0)


# ---------- isolamento e autenticação (RNF-001) ----------

def test_user_cannot_touch_another_users_card(client):
    owner, _, owner_card_account, owner_category, card_id = _setup(client, "cc32owner@example.com")
    intruder = _register_and_login(client, "cc32intruder@example.com")
    intruder_category = client.post("/categories", json={"name": "X"}, headers=intruder).json()["id"]
    entry = _buy(client, owner, card_id, owner_category).json()[0]
    payment_id = _pay(client, owner, card_id, MARCH, amount="10.00", paid_at="2026-03-10").json()["payments"][0]["id"]

    assert client.get(f"/cards/{card_id}", headers=intruder).status_code == 404
    assert client.patch(f"/cards/{card_id}", json={"due_day": 1}, headers=intruder).status_code == 404
    assert client.get(f"/cards/{card_id}/invoices", headers=intruder).status_code == 404
    assert client.get(f"/cards/{card_id}/invoices/{MARCH}", headers=intruder).status_code == 404
    assert _buy(client, intruder, card_id, intruder_category).status_code == 404
    assert client.patch(f"/cards/{card_id}/purchases/{entry['transaction_id']}", json={"invoice_closing_date": APRIL}, headers=intruder).status_code == 404
    assert _pay(client, intruder, card_id, MARCH, paid_at="2026-03-10").status_code == 404
    assert client.delete(f"/cards/{card_id}/invoices/{MARCH}/payments/{payment_id}", headers=intruder).status_code == 404
    assert client.get("/cards", headers=intruder).json() == []
    assert client.get("/cards/summary", headers=intruder).json()["debt"] == "0.00"
    # nem configurar cartão sobre a conta de outro usuário
    assert client.post("/cards", json={"account_id": owner_card_account, "closing_day": 5, "due_day": 12}, headers=intruder).status_code == 404
    assert len(client.get("/transfers", headers=owner).json()) == 1


def test_requires_authentication(client):
    assert client.get("/cards").status_code == 401
    assert client.get("/cards/summary").status_code == 401
    assert client.post("/cards", json={}).status_code == 401
