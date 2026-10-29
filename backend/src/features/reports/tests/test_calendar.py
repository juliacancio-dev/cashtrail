"""Marco 16 (doc 32, decisão 4): calendário do dinheiro, saldo em caixa dia a dia.

Mesmo `today` fixo dos outros testes de reports (20/08/2026).
"""

from datetime import date, timedelta

from src.features.reports import balances_dre, calendar_view, cash_flow

from .conftest_helpers import D, TODAY, make_world


def _cal(db, w, month="2026-08"):
    return calendar_view.build_calendar(db, w.user_id, cash_flow.parse_month(month), today=TODAY)


def _day(cal, day):
    return next(d for d in cal.days if d.day == date.fromisoformat(day))


def _scenario(client, email):
    """Mês com realizado, transferência para fora do caixa, compra e fatura, conta a pagar e recorrência."""
    w = make_world(client, email)  # 1000 + 500 = 1500 em caixa
    w.tx(w.checking, w.salary, "income", "3000.00", "2026-08-05", "Salário")
    w.tx(w.checking, w.market, "expense", "400.00", "2026-08-08", "Mercado")
    w.post("/transfers", from_account_id=w.checking, to_account_id=w.savings, amount="300.00", occurred_at="2026-08-10")
    w.post(f"/cards/{w.card_id}/purchases", description="TV", amount="900.00", purchase_date="2026-08-12", category_id=w.market)
    w.post("/commitments", direction="payable", description="Internet", amount="120.00", due_date="2026-08-25", category_id=w.rent)
    w.post("/commitments", direction="payable", description="IPTU", amount="200.00", due_date="2026-07-10", category_id=w.rent)
    w.post("/recurring", account_id=w.checking, category_id=w.rent, type="expense", amount="1000.00",
           frequency="monthly", next_occurrence_date="2026-08-28", description="Aluguel")
    return w


# ---------- propriedades (decisão 4) ----------

def test_cash_today_equals_the_cash_total_of_balances(client, db_session):
    w = _scenario(client, "cal1@example.com")

    cal = _cal(db_session, w)

    assert cal.cash_today == balances_dre.balances(db_session, w.user_id, today=TODAY).cash_total == D("4100.00")


def test_each_day_is_the_previous_plus_its_net_and_the_month_closes_on_the_last_day(client, db_session):
    w = _scenario(client, "cal2@example.com")

    cal = _cal(db_session, w)

    previous = cal.opening_balance
    for day in cal.days:
        assert day.balance == previous + day.net, day.day
        assert day.net == sum((e.amount if e.direction == "in" else -e.amount for e in day.events), D("0"))
        previous = day.balance
    assert cal.closing_balance == cal.days[-1].balance
    assert cal.opening_balance + sum((d.net for d in cal.days), D("0")) == cal.closing_balance


def test_next_month_opens_where_this_month_closed(client, db_session):
    w = _scenario(client, "cal3@example.com")

    august, september = _cal(db_session, w, "2026-08"), _cal(db_session, w, "2026-09")

    assert september.opening_balance == august.closing_balance


def test_month_closing_matches_the_projected_closing_of_the_cash_flow(client, db_session):
    w = _scenario(client, "cal4@example.com")

    flow = cash_flow.build_cash_flow(db_session, w.user_id, cash_flow.parse_month("2026-08"), 2, today=TODAY)

    for key in ("2026-08", "2026-09"):
        month = next(m for m in flow.months if m.month == key)
        assert _cal(db_session, w, key).closing_balance == month.closing_projected, key


# ---------- regras de dinheiro ----------

def test_card_purchase_does_not_touch_cash_and_internal_transfer_does_not_change_the_balance(client, db_session):
    w = _scenario(client, "cal5@example.com")

    cal = _cal(db_session, w)

    assert _day(cal, "2026-08-12").net == D("0.00")  # compra no cartão (a fatura vence em 12/09)
    assert _day(cal, "2026-08-10").net == D("0.00")  # corrente → poupança
    assert _day(cal, "2026-08-05").balance == D("4500.00")


def test_overdue_and_due_today_items_fall_on_today_as_planned(client, db_session):
    w = _scenario(client, "cal6@example.com")

    today = _day(_cal(db_session, w), "2026-08-20")

    assert today.status == "today"
    assert [(e.kind, e.description, e.amount) for e in today.events] == [("planned", "IPTU", D("200.00"))]
    assert today.balance == D("3900.00")  # 4100 em caixa − IPTU vencido


def test_future_days_carry_what_remains_of_the_planned_items(client, db_session):
    w = _scenario(client, "cal7@example.com")

    cal = _cal(db_session, w)

    assert _day(cal, "2026-08-25").events[0].description == "Internet"
    assert _day(cal, "2026-08-25").balance == D("3780.00")
    assert _day(cal, "2026-08-28").balance == D("2780.00")  # aluguel recorrente
    assert [d.status for d in cal.days[18:21]] == ["past", "today", "future"]


def test_partial_payment_leaves_only_the_rest_in_the_future(client, db_session):
    w = make_world(client, "cal8@example.com")
    bill = w.post("/commitments", direction="payable", description="Reforma", amount="1000.00", due_date="2026-08-30", category_id=w.rent)[0]
    w.post(f"/commitments/{bill['id']}/settlements", account_id=w.checking, amount="400.00", paid_at="2026-08-15")

    cal = _cal(db_session, w)

    assert _day(cal, "2026-08-15").net == D("-400.00")
    assert _day(cal, "2026-08-30").net == D("-600.00")
    assert cal.closing_balance == D("500.00")


def test_past_month_is_only_realized(client, db_session):
    w = _scenario(client, "cal9@example.com")

    july = _cal(db_session, w, "2026-07")

    assert all(d.status == "past" and all(e.kind == "realized" for e in d.events) for d in july.days)
    assert july.closing_balance == D("1500.00")  # o IPTU vencido em julho não mexe no passado


# ---------- dia mais apertado e dias apertados ----------

def test_tightest_day_is_the_lowest_balance_and_the_first_on_ties(client, db_session):
    w = _scenario(client, "cal10@example.com")

    cal = _cal(db_session, w)

    assert (cal.tightest_day, cal.tightest_balance) == (date(2026, 8, 1), D("1500.00"))
    lowest_after_salary = min((d for d in cal.days if d.day >= date(2026, 8, 5)), key=lambda d: d.balance)
    assert lowest_after_salary.day == date(2026, 8, 28)  # empata até o dia 31; vale o primeiro


def test_tight_days_are_the_lowest_quarter_of_the_month(client, db_session):
    w = _scenario(client, "cal11@example.com")

    cal = _cal(db_session, w)

    tight = [d.day.day for d in cal.days if d.is_tight]
    assert tight == [1, 2, 3, 4, 28, 29, 30, 31]  # ceil(31/4) = 8 dias, os de menor saldo


def test_month_without_movements_has_no_tight_day(client, db_session):
    w = make_world(client, "cal12@example.com")

    cal = _cal(db_session, w)

    assert not any(d.is_tight for d in cal.days)
    assert len(cal.days) == 31 and cal.closing_balance == D("1500.00")


# ---------- API ----------

def test_calendar_endpoint_shape_validation_and_isolation(client, db_session):
    w = _scenario(client, "cal13@example.com")
    other = make_world(client, "cal14@example.com")

    body = w.get("/reports/calendar", month="2026-02").json()
    assert body["month"] == "2026-02" and len(body["days"]) == 28
    assert set(body["days"][0]) == {"day", "status", "balance", "net", "is_tight", "events"}
    assert client.get("/reports/calendar", params={"month": "2026-13"}, headers=w.headers).status_code == 422
    assert client.get("/reports/calendar").status_code == 401

    other_days = other.get("/reports/calendar", month="2026-08").json()["days"]
    assert all(d["events"] == [] for d in other_days)  # nada do outro usuário vaza


def test_calendar_defaults_to_the_current_month(client, db_session):
    w = make_world(client, "cal15@example.com")

    body = w.get("/reports/calendar").json()

    assert body["month"] == f"{date.today():%Y-%m}"
    assert body["today"] == date.today().isoformat()
    assert sum(1 for d in body["days"] if d["status"] == "today") == 1
    assert (date.fromisoformat(body["days"][-1]["day"]) + timedelta(days=1)).day == 1
