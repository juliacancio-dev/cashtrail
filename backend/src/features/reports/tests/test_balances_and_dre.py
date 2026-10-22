"""RF-031 (saldos) e RF-033 (DRE)."""

from datetime import date
from decimal import Decimal

import pytest

from src.features.reports import balances_dre

from .conftest_helpers import D, TODAY, make_world


def _line(dre, key):
    return next(line for line in dre.lines if line.key == key)


# ---------- saldos ----------

def test_balance_is_opening_plus_movements_up_to_today(client, db_session):
    w = make_world(client, "rb1@example.com")
    w.tx(w.checking, w.salary, "income", "3000.00", "2026-08-05")
    w.tx(w.checking, w.market, "expense", "450.00", "2026-08-10")
    w.tx(w.checking, w.rent, "expense", "999.00", "2026-09-10")  # futuro: ainda não mexeu no saldo

    result = balances_dre.balances(db_session, w.user_id, today=TODAY)

    by_name = {a.name: a for a in result.accounts}
    assert by_name["Corrente"].balance == D("3550.00")   # 1000 + 3000 − 450
    assert by_name["Poupança"].balance == D("500.00")
    assert result.cash_total == D("4050.00")


def test_transfers_move_balance_between_accounts_without_changing_cash_total(client, db_session):
    w = make_world(client, "rb2@example.com")
    w.post("/transfers", from_account_id=w.checking, to_account_id=w.savings, amount="200.00", occurred_at="2026-08-01")

    result = balances_dre.balances(db_session, w.user_id, today=TODAY)

    by_name = {a.name: a.balance for a in result.accounts}
    assert (by_name["Corrente"], by_name["Poupança"]) == (D("800.00"), D("700.00"))
    assert result.cash_total == D("1500.00")


def test_card_balance_is_negative_debt_and_not_part_of_cash(client, db_session):
    w = make_world(client, "rb3@example.com")
    w.post(f"/cards/{w.card_id}/purchases", description="TV", amount="400.00", purchase_date="2026-08-03", category_id=w.market)

    result = balances_dre.balances(db_session, w.user_id, today=TODAY)

    card = next(a for a in result.accounts if a.name == "Cartão")
    assert card.balance == D("-400.00")
    assert result.card_debt_total == D("400.00")
    assert result.cash_total == D("1500.00")  # a compra no cartão não saiu do caixa


def test_paying_the_card_reduces_cash_and_debt(client, db_session):
    w = make_world(client, "rb4@example.com")
    w.post(f"/cards/{w.card_id}/purchases", description="TV", amount="400.00", purchase_date="2026-08-03", category_id=w.market)
    w.post(f"/cards/{w.card_id}/invoices/2026-08-05/payments", amount="400.00", paid_at="2026-08-12")

    result = balances_dre.balances(db_session, w.user_id, today=TODAY)

    by_name = {a.name: a.balance for a in result.accounts}
    assert by_name["Corrente"] == D("600.00")
    assert by_name["Cartão"] == D("0.00")
    assert (result.cash_total, result.card_debt_total) == (D("1100.00"), D("0.00"))


# ---------- DRE ----------

def test_dre_builds_the_groups_subtotals_and_net_result(client, db_session):
    w = make_world(client, "rd1@example.com")
    w.tx(w.checking, w.salary, "income", "5000.00", "2026-08-05")
    w.tx(w.checking, w.market, "expense", "800.00", "2026-08-10")
    w.tx(w.checking, w.rent, "expense", "1500.00", "2026-08-06")
    fin = w.post("/categories", name="Juros", dre_group="financial_expense")["id"]
    ded = w.post("/categories", name="INSS", dre_group="deduction")["id"]
    w.tx(w.checking, fin, "expense", "50.00", "2026-08-15")
    w.tx(w.checking, ded, "expense", "500.00", "2026-08-05")

    result = balances_dre.dre(db_session, w.user_id, date(2026, 8, 1), date(2026, 8, 31))

    assert _line(result, "revenue").amount == D("5000.00")
    assert _line(result, "deduction").amount == D("500.00")
    assert _line(result, "net_revenue").amount == D("4500.00")
    assert _line(result, "gross_result").amount == D("3700.00")        # − variáveis 800
    assert _line(result, "operating_result").amount == D("2200.00")    # − fixas 1500
    assert result.net_result == D("2150.00")                            # − financeiras 50
    assert _line(result, "variable_expense").percent_of_net_revenue == D("17.78")  # 800 / 4500


def test_dre_net_result_always_equals_income_minus_expense(client, db_session):
    """Propriedade: independente de grupos, o resultado fecha com receitas − despesas."""
    w = make_world(client, "rd2@example.com")
    w.tx(w.checking, w.salary, "income", "1000.00", "2026-08-02")
    w.tx(w.checking, w.ungrouped, "income", "40.00", "2026-08-03")
    w.tx(w.checking, w.market, "expense", "123.45", "2026-08-04")
    w.tx(w.checking, w.rent, "expense", "700.00", "2026-08-05")
    w.tx(w.checking, w.ungrouped, "expense", "9.99", "2026-08-06")
    w.tx(w.checking, w.market, "income", "30.00", "2026-08-07")     # estorno em categoria de despesa
    w.tx(w.checking, w.salary, "expense", "15.00", "2026-08-08")    # ajuste em categoria de receita

    result = balances_dre.dre(db_session, w.user_id, date(2026, 8, 1), date(2026, 8, 31))

    income, expense = D("1000.00") + D("40.00") + D("30.00"), D("123.45") + D("700.00") + D("9.99") + D("15.00")
    assert result.net_result == income - expense


def test_opposite_direction_nets_inside_the_group(client, db_session):
    w = make_world(client, "rd3@example.com")
    w.tx(w.checking, w.market, "expense", "200.00", "2026-08-04")
    w.tx(w.checking, w.market, "income", "50.00", "2026-08-05")   # estorno

    result = balances_dre.dre(db_session, w.user_id, date(2026, 8, 1), date(2026, 8, 31))

    assert _line(result, "variable_expense").amount == D("150.00")


def test_transfers_never_appear_in_the_dre(client, db_session):
    w = make_world(client, "rd4@example.com")
    w.tx(w.checking, w.salary, "income", "1000.00", "2026-08-02")
    before = balances_dre.dre(db_session, w.user_id, date(2026, 8, 1), date(2026, 8, 31)).net_result

    w.post("/transfers", from_account_id=w.checking, to_account_id=w.savings, amount="400.00", occurred_at="2026-08-03")
    w.post("/transfers", from_account_id=w.checking, to_account_id=w.card_account, amount="100.00", occurred_at="2026-08-04")

    assert balances_dre.dre(db_session, w.user_id, date(2026, 8, 1), date(2026, 8, 31)).net_result == before


def test_card_purchase_hits_the_dre_on_the_purchase_date_and_payment_does_not(client, db_session):
    w = make_world(client, "rd5@example.com")
    w.post(f"/cards/{w.card_id}/purchases", description="TV", amount="300.00", purchase_date="2026-07-20", category_id=w.market)
    w.post(f"/cards/{w.card_id}/invoices/2026-08-05/payments", amount="300.00", paid_at="2026-08-12")

    july = balances_dre.dre(db_session, w.user_id, date(2026, 7, 1), date(2026, 7, 31))
    august = balances_dre.dre(db_session, w.user_id, date(2026, 8, 1), date(2026, 8, 31))

    assert _line(july, "variable_expense").amount == D("300.00")  # competência: mês da compra
    assert august.net_result == D("0.00")                          # pagar a fatura não é despesa


def test_ungrouped_categories_are_listed_apart_and_still_counted(client, db_session):
    w = make_world(client, "rd6@example.com")
    w.tx(w.checking, w.ungrouped, "expense", "80.00", "2026-08-04")
    w.tx(w.checking, w.ungrouped, "income", "20.00", "2026-08-05")

    result = balances_dre.dre(db_session, w.user_id, date(2026, 8, 1), date(2026, 8, 31))

    assert _line(result, "ungrouped_expense").amount == D("80.00")
    assert _line(result, "ungrouped_income").amount == D("20.00")
    assert [c.name for c in _line(result, "ungrouped_expense").categories] == ["Diversos"]
    assert result.ungrouped_count == 2
    assert result.net_result == D("-60.00")


def test_dre_compares_with_the_previous_period(client, db_session):
    w = make_world(client, "rd7@example.com")
    w.tx(w.checking, w.salary, "income", "4000.00", "2026-07-05")
    w.tx(w.checking, w.salary, "income", "5000.00", "2026-08-05")

    result = balances_dre.dre(db_session, w.user_id, date(2026, 8, 1), date(2026, 8, 31))

    revenue = _line(result, "revenue")
    assert (revenue.amount, revenue.previous_amount) == (D("5000.00"), D("4000.00"))
    # mês inteiro compara com o mês anterior inteiro: 01/07 a 31/07
    assert (result.previous_start_date, result.previous_end_date) == (date(2026, 7, 1), date(2026, 7, 31))
    assert result.previous_net_result == D("4000.00")


def test_dre_of_a_31_day_month_compares_with_the_whole_previous_month(client, db_session):
    # outubro (31 dias) contra setembro (30): antes comparava com 31/08 a 30/09 e contava o 31/08
    w = make_world(client, "rd7b@example.com")
    w.tx(w.checking, w.salary, "income", "700.00", "2026-08-31")
    w.tx(w.checking, w.salary, "income", "4000.00", "2026-09-05")
    w.tx(w.checking, w.salary, "income", "5000.00", "2026-10-05")

    result = balances_dre.dre(db_session, w.user_id, date(2026, 10, 1), date(2026, 10, 31))

    assert (result.previous_start_date, result.previous_end_date) == (date(2026, 9, 1), date(2026, 9, 30))
    assert _line(result, "revenue").previous_amount == D("4000.00")


@pytest.mark.parametrize(
    ("start", "end", "expected"),
    [
        # meses inteiros: mesmo número de meses inteiros, mesmo com tamanhos diferentes
        (date(2026, 10, 1), date(2026, 10, 31), (date(2026, 9, 1), date(2026, 9, 30))),
        (date(2026, 3, 1), date(2026, 3, 31), (date(2026, 2, 1), date(2026, 2, 28))),
        (date(2026, 1, 1), date(2026, 1, 31), (date(2025, 12, 1), date(2025, 12, 31))),
        (date(2026, 10, 1), date(2026, 12, 31), (date(2026, 7, 1), date(2026, 9, 30))),
        (date(2026, 1, 1), date(2026, 12, 31), (date(2025, 1, 1), date(2025, 12, 31))),
        # outro período: mesmo número de dias, terminando na véspera
        (date(2026, 10, 10), date(2026, 10, 19), (date(2026, 9, 30), date(2026, 10, 9))),
        (date(2026, 10, 1), date(2026, 10, 15), (date(2026, 9, 16), date(2026, 9, 30))),
        (date(2026, 10, 1), date(2026, 10, 1), (date(2026, 9, 30), date(2026, 9, 30))),
    ],
)
def test_previous_period(start, end, expected):
    assert balances_dre.previous_period(start, end) == expected


def test_include_forecast_adds_open_commitments_by_due_date(client, db_session):
    w = make_world(client, "rd8@example.com")
    w.tx(w.checking, w.salary, "income", "1000.00", "2026-08-02")
    open_bill = w.post("/commitments", direction="payable", description="Aluguel", amount="600.00", due_date="2026-08-25", category_id=w.rent)
    paid = w.post("/commitments", direction="payable", description="Luz", amount="100.00", due_date="2026-08-10", category_id=w.rent)[0]
    w.post(f"/commitments/{paid['id']}/settlements", account_id=w.checking, paid_at="2026-08-10")
    assert open_bill[0]["status"] in ("open", "overdue", "due_today")

    realized = balances_dre.dre(db_session, w.user_id, date(2026, 8, 1), date(2026, 8, 31))
    forecast = balances_dre.dre(db_session, w.user_id, date(2026, 8, 1), date(2026, 8, 31), include_forecast=True)

    assert _line(realized, "fixed_expense").amount == D("100.00")             # só a luz, já paga
    assert _line(forecast, "fixed_expense").amount == D("700.00")             # + o aluguel em aberto
    assert forecast.net_result == realized.net_result - D("600.00")


def test_dre_is_isolated_per_user(client, db_session):
    owner = make_world(client, "rd9owner@example.com")
    other = make_world(client, "rd9other@example.com")
    owner.tx(owner.checking, owner.salary, "income", "9999.00", "2026-08-02")

    result = balances_dre.dre(db_session, other.user_id, date(2026, 8, 1), date(2026, 8, 31))

    assert result.net_result == Decimal("0.00")
    assert _line(result, "revenue").categories == []
