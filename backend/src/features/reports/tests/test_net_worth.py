"""Balanço patrimonial (Marco 12): PL = caixa + bens − cartões − dívidas, calculado do histórico."""

from datetime import date, timedelta
from decimal import Decimal

from .conftest_helpers import make_world

D = Decimal
TODAY = date.today()


def world(client, email):
    w = make_world(client, email)  # corrente 1000 + poupança 500 = 1500 de caixa
    w.interest = w.post("/categories", name="Juros", dre_group="financial_expense")["id"]
    return w


def worth(w, **params):
    return w.get("/reports/net-worth", **params).json()


def new_debt(w, **overrides):
    body = dict(
        name="Empréstimo",
        principal="1000.00",
        contracted_at=TODAY.isoformat(),
        installments=12,
        first_due_date=(TODAY + timedelta(days=10)).isoformat(),
        system="price",
        monthly_rate="2",
        interest_category_id=w.interest,
        payment_account_id=w.checking,
        received_account_id=w.checking,
    )
    body.update(overrides)
    return w.post("/debts", **body)


def test_net_worth_is_cash_plus_assets_minus_cards_and_debts(client):
    w = world(client, "n1@example.com")
    w.post("/assets", name="Carro", kind="vehicle", current_value="30000.00")
    w.tx(w.card_account, w.market, "expense", "200.00", TODAY.isoformat())  # dívida de cartão

    body = worth(w)

    assert body["cash_total"] == "1500.00"
    assert body["assets_total"] == "30000.00"
    assert body["cards_total"] == "200.00"
    assert body["total_assets"] == "31500.00"
    assert body["total_liabilities"] == "200.00"
    assert body["net_worth"] == "31300.00"


def test_receiving_a_loan_does_not_change_net_worth_and_paying_costs_only_the_charges(client):
    w = world(client, "n2@example.com")
    before = D(worth(w)["net_worth"])

    debt = new_debt(w)
    after_loan = worth(w)
    w.post(f"/debts/{debt['id']}/installments/{debt['installment_list'][0]['id']}/payment")
    after_payment = worth(w)

    assert D(after_loan["net_worth"]) == before  # +1000 de caixa, −1000 de dívida
    assert after_loan["debts_total"] == "1000.00"
    assert D(after_payment["net_worth"]) == before - D("20.00")  # só os juros da 1ª parcela (RB-029)


def test_transfers_and_card_payments_do_not_move_net_worth(client):
    w = world(client, "n3@example.com")
    w.tx(w.card_account, w.market, "expense", "300.00", TODAY.isoformat())
    base = D(worth(w)["net_worth"])

    w.post("/transfers", from_account_id=w.checking, to_account_id=w.savings, amount="200.00",
           occurred_at=TODAY.isoformat())
    w.post("/transfers", from_account_id=w.checking, to_account_id=w.card_account, amount="300.00",
           occurred_at=TODAY.isoformat())

    after = worth(w)
    assert D(after["net_worth"]) == base
    assert after["cards_total"] == "0.00"


def test_history_excludes_assets_before_their_first_valuation(client):
    w = world(client, "n4@example.com")
    first_of_month = TODAY.replace(day=1)
    valued_at = first_of_month - timedelta(days=1)  # no mês passado
    w.post("/assets", name="Casa", kind="real_estate", current_value="200000.00", valued_at=valued_at.isoformat())

    points = w.get("/reports/net-worth/history", months=3).json()

    assert len(points) == 3
    assert points[-1]["month"] == TODAY.strftime("%Y-%m")
    assert points[-1]["as_of"] == TODAY.isoformat()
    assert D(points[-1]["net_worth"]) == D("201500.00")
    assert D(points[-2]["net_worth"]) == D("201500.00")  # avaliada no último dia do mês passado
    assert D(points[0]["net_worth"]) == D("1500.00")  # antes da avaliação (RB-030)


def test_long_term_debt_splits_the_principal_due_within_twelve_months(client):
    w = world(client, "n5@example.com")
    new_debt(w, principal="12000.00", installments=24, monthly_rate="1", received_account_id=None)

    body = worth(w)

    short, long = D(body["debts_short_term"]), D(body["debts_long_term"])
    assert short > 0 and long > 0
    assert short + long == D(body["debts_total"]) == D("12000.00")


def test_financed_asset_shows_equity(client):
    w = world(client, "n6@example.com")
    debt = new_debt(w, principal="10000.00", installments=24, received_account_id=None)
    w.post("/assets", name="Carro", kind="vehicle", current_value="30000.00", debt_id=debt["id"])

    asset = worth(w)["assets"][0]

    assert asset["debt_outstanding"] == "10000.00"
    assert asset["equity"] == "20000.00"


def test_future_as_of_is_rejected(client):
    w = world(client, "n7@example.com")

    response = client.get(
        "/reports/net-worth", params={"as_of": (TODAY + timedelta(days=1)).isoformat()}, headers=w.headers
    )

    assert response.status_code == 422


def test_csv_has_bom_and_neutralizes_formula_names(client):
    w = world(client, "n8@example.com")
    w.post("/assets", name="=HYPERLINK(\"http://evil\")", kind="other", current_value="10.00")

    response = client.get("/reports/net-worth.csv", headers=w.headers)

    assert response.status_code == 200
    text = response.content.decode("utf-8")
    assert text.startswith("﻿")
    assert "'=HYPERLINK" in text
    assert "Patrimônio líquido" in text


def test_net_worth_is_isolated_between_users(client):
    a = world(client, "n9a@example.com")
    b = world(client, "n9b@example.com")
    a.post("/assets", name="Casa", kind="real_estate", current_value="500000.00")

    assert worth(b)["assets_total"] == "0.00"
