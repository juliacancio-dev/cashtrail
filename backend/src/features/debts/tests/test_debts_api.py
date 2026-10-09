"""Dívidas (Marco 11) pela API: o principal nunca vira receita nem despesa (RB-023), só os encargos."""

from datetime import date, timedelta
from decimal import Decimal

from src.features.reports.tests.conftest_helpers import make_world

D = Decimal
TODAY = date.today()
FIRST_DUE = TODAY + timedelta(days=10)
MONTH_START = TODAY.replace(day=1).isoformat()


def world(client, email):
    w = make_world(client, email, checking_opening="5000.00", savings_opening="0.00")
    w.interest = w.post("/categories", name="Juros do empréstimo", dre_group="financial_expense")["id"]
    return w


def new_debt(w, **overrides):
    body = dict(
        name="Empréstimo pessoal",
        creditor="Banco X",
        principal="1000.00",
        contracted_at=TODAY.isoformat(),
        installments=12,
        first_due_date=FIRST_DUE.isoformat(),
        system="price",
        monthly_rate="2",
        interest_category_id=w.interest,
        payment_account_id=w.checking,
        received_account_id=w.checking,
    )
    body.update(overrides)
    return w.post("/debts", **body)


def balances(w):
    body = w.get("/reports/balances").json()
    return {a["name"]: D(a["balance"]) for a in body["accounts"]}, body


def dre(w):
    return w.get("/reports/dre", start_date=MONTH_START, end_date=TODAY.isoformat()).json()


def installments(w, debt_id):
    return w.get(f"/debts/{debt_id}").json()["installment_list"]


def test_preview_does_not_persist_anything(client):
    w = world(client, "d1@example.com")

    body = w.post(
        "/debts/preview", principal="1000.00", installments=12, first_due_date=FIRST_DUE.isoformat(),
        system="price", monthly_rate="2",
    )

    assert body["rows"][0]["amount"] == "94.56"
    assert D(body["total_charges"]) == D(body["total_paid"]) - D("1000.00")
    assert w.get("/debts").json() == []


def test_receiving_the_money_is_a_transfer_not_income(client):
    w = world(client, "d2@example.com")

    debt = new_debt(w)

    by_name, body = balances(w)
    assert by_name["Corrente"] == D("6000.00")  # 5000 + 1000 recebidos
    assert by_name["Empréstimo pessoal"] == D("-1000.00")
    assert body["loan_debt_total"] == "1000.00"
    assert body["cash_total"] == "6000.00"  # a conta da dívida não é caixa
    assert debt["outstanding"] == "1000.00"
    assert debt["installments_open"] == 12
    report = dre(w)
    assert report["net_result"] == "0.00"  # nem receita nem despesa


def test_existing_debt_without_received_account_starts_negative(client):
    w = world(client, "d3@example.com")

    debt = new_debt(w, received_account_id=None)

    by_name, _ = balances(w)
    assert by_name["Corrente"] == D("5000.00")
    assert debt["outstanding"] == "1000.00"


def test_paying_an_installment_expenses_only_the_charges(client):
    w = world(client, "d4@example.com")
    debt = new_debt(w)
    first = debt["installment_list"][0]
    assert (first["amount"], first["principal_part"], first["charges"]) == ("94.56", "74.56", "20.00")

    paid = w.post(f"/debts/{debt['id']}/installments/{first['id']}/payment")

    assert paid["status"] == "paid"
    by_name, _ = balances(w)
    assert by_name["Corrente"] == D("6000.00") - D("94.56")  # saiu a parcela inteira
    assert by_name["Empréstimo pessoal"] == D("-925.44")  # 1000 − 74.56 de principal
    report = dre(w)
    assert report["net_result"] == "-20.00"  # só os juros são despesa
    fin = next(line for line in report["lines"] if line["key"] == "financial_expense")
    assert fin["amount"] == "20.00"
    detail = w.get(f"/debts/{debt['id']}").json()
    assert detail["outstanding"] == "925.44"
    assert detail["principal_paid"] == "74.56"
    assert detail["charges_paid"] == "20.00"
    assert detail["installments_paid"] == 1


def test_undoing_a_payment_restores_balance_and_dre(client):
    w = world(client, "d5@example.com")
    debt = new_debt(w)
    first = debt["installment_list"][0]
    w.post(f"/debts/{debt['id']}/installments/{first['id']}/payment")

    response = client.delete(
        f"/debts/{debt['id']}/installments/{first['id']}/payment", headers=w.headers
    )

    assert response.status_code == 200
    assert response.json()["status"] != "paid"
    by_name, _ = balances(w)
    assert by_name["Corrente"] == D("6000.00")
    assert by_name["Empréstimo pessoal"] == D("-1000.00")
    assert dre(w)["net_result"] == "0.00"


def test_generic_commitment_endpoints_refuse_debt_installments(client):
    w = world(client, "d6@example.com")
    debt = new_debt(w)
    commitment_id = debt["installment_list"][0]["commitment_id"]

    settle = client.post(
        f"/commitments/{commitment_id}/settlements", json={"account_id": w.checking}, headers=w.headers
    )
    edit = client.patch(f"/commitments/{commitment_id}", json={"amount": "10.00"}, headers=w.headers)
    cancel = client.post(f"/commitments/{commitment_id}/cancel", headers=w.headers)

    assert (settle.status_code, edit.status_code, cancel.status_code) == (409, 409, 409)


def test_installment_amount_cannot_go_below_its_principal(client):
    w = world(client, "d7@example.com")
    debt = new_debt(w)
    first = debt["installment_list"][0]
    url = f"/debts/{debt['id']}/installments/{first['id']}"

    too_low = client.patch(url, json={"amount": "70.00"}, headers=w.headers)
    higher = client.patch(url, json={"amount": "100.00"}, headers=w.headers)

    assert too_low.status_code == 422
    assert higher.status_code == 200
    assert (higher.json()["principal_part"], higher.json()["charges"]) == ("74.56", "25.44")


def test_extra_amortization_reducing_the_term_keeps_the_installment(client):
    w = world(client, "d8@example.com")
    debt = new_debt(w)
    before = debt["installment_list"]

    preview = w.post(f"/debts/{debt['id']}/amortization-preview", amount="400.00", mode="reduce_term")
    result = w.post(f"/debts/{debt['id']}/amortizations", amount="400.00", mode="reduce_term")

    after = result["installment_list"]
    assert preview["installments_after"] == len(after) < len(before)
    assert after[0]["amount"] == before[0]["amount"]  # mantém a parcela
    assert D(preview["charges_after"]) < D(preview["charges_before"])
    assert result["outstanding"] == "600.00"
    assert sum(D(i["principal_part"]) for i in after) == D("600.00")
    by_name, _ = balances(w)
    assert by_name["Corrente"] == D("5600.00")  # 6000 − 400 de amortização
    assert dre(w)["net_result"] == "0.00"  # amortizar principal não é despesa


def test_extra_amortization_reducing_the_installment_keeps_the_term(client):
    w = world(client, "d9@example.com")
    debt = new_debt(w)
    before = debt["installment_list"]

    result = w.post(f"/debts/{debt['id']}/amortizations", amount="400.00", mode="reduce_installment")

    after = result["installment_list"]
    assert len(after) == len(before)
    assert D(after[0]["amount"]) < D(before[0]["amount"])
    assert sum(D(i["principal_part"]) for i in after) == D("600.00")


def test_amortization_above_the_outstanding_balance_is_rejected(client):
    w = world(client, "d10@example.com")
    debt = new_debt(w)

    response = client.post(
        f"/debts/{debt['id']}/amortizations", json={"amount": "1000.01", "mode": "reduce_term"}, headers=w.headers
    )

    assert response.status_code == 422


def test_payoff_zeroes_the_debt_and_cancels_open_installments(client):
    w = world(client, "d11@example.com")
    debt = new_debt(w)
    first = debt["installment_list"][0]
    w.post(f"/debts/{debt['id']}/installments/{first['id']}/payment")

    result = w.post(f"/debts/{debt['id']}/amortizations", mode="payoff")

    assert result["outstanding"] == "0.00"
    assert result["is_paid_off"] is True
    by_name, body = balances(w)
    assert by_name["Empréstimo pessoal"] == D("0.00")
    assert body["loan_debt_total"] == "0.00"
    open_items = w.get("/commitments", status="pending").json()["items"]
    assert open_items == []
    again = client.post(f"/debts/{debt['id']}/amortizations", json={"mode": "payoff"}, headers=w.headers)
    assert again.status_code == 409


def test_summary_totals_the_outstanding_balance(client):
    w = world(client, "d12@example.com")
    new_debt(w)
    new_debt(w, name="Financiamento", principal="3000.00", monthly_rate="1")

    body = w.get("/debts/summary").json()

    assert body["outstanding_total"] == "4000.00"
    assert body["active_count"] == 2
    assert body["next_due_date"] == FIRST_DUE.isoformat()


def test_cash_flow_counts_loan_money_and_installments_as_cash(client):
    w = world(client, "d13@example.com")
    new_debt(w)

    flow = w.get("/reports/cash-flow", start_month=TODAY.strftime("%Y-%m"), months=3).json()

    assert flow["cash_balance_today"] == "6000.00"
    total_planned = sum(D(m["planned_out"]) for m in flow["months"])
    assert total_planned >= D("94.56")  # as parcelas entram como saídas previstas


def test_debts_are_isolated_between_users(client):
    a = world(client, "d14a@example.com")
    b = world(client, "d14b@example.com")
    debt = new_debt(a)

    response = client.get(f"/debts/{debt['id']}", headers=b.headers)

    assert response.status_code == 404
    assert b.get("/debts").json() == []
