"""RF-034 a RF-036: fluxo de caixa realizado, previsto e projetado.

`today` fixo em 20/08/2026: tudo que a API valida contra o relógio real (data de pagamento
não pode ser futura) continua válido, e os relatórios não dependem do dia da execução.
"""

from datetime import date

from src.features.reports import cash_flow

from .conftest_helpers import D, TODAY, make_world


def _flow(db, w, start="2026-07", months=6):
    return cash_flow.build_cash_flow(db, w.user_id, cash_flow.parse_month(start), months, today=TODAY)


def _month(flow, key):
    return next(m for m in flow.months if m.month == key)


# ---------- realizado (caixa) ----------

def test_realized_counts_cash_account_movements_and_card_payments_not_card_purchases(client, db_session):
    w = make_world(client, "cf1@example.com")
    w.tx(w.checking, w.salary, "income", "3000.00", "2026-08-05")
    w.tx(w.checking, w.market, "expense", "400.00", "2026-08-08")
    w.post(f"/cards/{w.card_id}/purchases", description="TV", amount="900.00", purchase_date="2026-08-02", category_id=w.market)

    august = _month(_flow(db_session, w), "2026-08")

    assert (august.realized_in, august.realized_out) == (D("3000.00"), D("400.00"))  # a compra de 900 não saiu do caixa


def test_card_invoice_payment_is_a_cash_outflow_in_the_month_it_is_paid(client, db_session):
    w = make_world(client, "cf2@example.com")
    w.post(f"/cards/{w.card_id}/purchases", description="TV", amount="900.00", purchase_date="2026-07-02", category_id=w.market)
    w.post(f"/cards/{w.card_id}/invoices/2026-07-05/payments", amount="900.00", paid_at="2026-08-12")

    flow = _flow(db_session, w)

    assert _month(flow, "2026-07").realized_out == D("0.00")
    assert _month(flow, "2026-08").realized_out == D("900.00")


def test_transfers_between_cash_accounts_do_not_change_the_flow(client, db_session):
    w = make_world(client, "cf3@example.com")
    before = _month(_flow(db_session, w), "2026-08")

    w.post("/transfers", from_account_id=w.checking, to_account_id=w.savings, amount="300.00", occurred_at="2026-08-04")
    after = _month(_flow(db_session, w), "2026-08")

    assert (after.realized_in, after.realized_out, after.closing_realized) == (
        before.realized_in, before.realized_out, before.closing_realized
    )


def test_balances_chain_from_opening_through_the_months(client, db_session):
    w = make_world(client, "cf4@example.com")  # 1000 + 500 = 1500 em caixa
    w.tx(w.checking, w.salary, "income", "3000.00", "2026-07-05")
    w.tx(w.checking, w.market, "expense", "500.00", "2026-07-20")
    w.tx(w.checking, w.salary, "income", "3000.00", "2026-08-05")

    flow = _flow(db_session, w)

    july, august = _month(flow, "2026-07"), _month(flow, "2026-08")
    assert july.closing_realized == D("4000.00")     # 1500 + 3000 − 500
    assert august.opening_balance == D("4000.00")     # o final de um mês é o inicial do seguinte
    assert august.closing_realized == D("7000.00")
    assert flow.cash_balance_today == D("7000.00")


def test_past_months_have_projected_equal_to_realized_and_future_have_no_realized(client, db_session):
    w = make_world(client, "cf5@example.com")
    w.tx(w.checking, w.salary, "income", "3000.00", "2026-07-05")

    flow = _flow(db_session, w)

    july, october = _month(flow, "2026-07"), _month(flow, "2026-10")
    assert july.status == "past" and _month(flow, "2026-08").status == "current" and october.status == "future"
    assert (july.projected_in, july.projected_out, july.closing_projected) == (
        july.realized_in, july.realized_out, july.closing_realized
    )
    assert october.closing_realized is None


# ---------- previsto × realizado ----------

def test_commitment_is_planned_in_the_due_month_and_realized_in_the_paid_month(client, db_session):
    w = make_world(client, "cf6@example.com")
    bill = w.post("/commitments", direction="payable", description="Internet", amount="300.00", due_date="2026-07-25", category_id=w.rent)[0]
    w.post(f"/commitments/{bill['id']}/settlements", account_id=w.checking, paid_at="2026-08-05")

    flow = _flow(db_session, w)

    july, august = _month(flow, "2026-07"), _month(flow, "2026-08")
    assert (july.planned_out, july.realized_out) == (D("300.00"), D("0.00"))
    assert (august.planned_out, august.realized_out) == (D("0.00"), D("300.00"))
    assert (july.variance_out, august.variance_out) == (D("-300.00"), D("300.00"))
    assert july.projected_out == D("0.00")  # já foi paga: nada resta para projetar em julho


def test_overdue_unpaid_commitment_is_planned_in_its_month_and_projected_today(client, db_session):
    w = make_world(client, "cf7@example.com")
    w.post("/commitments", direction="payable", description="IPTU", amount="200.00", due_date="2026-07-10", category_id=w.rent)

    flow = _flow(db_session, w)

    july, august = _month(flow, "2026-07"), _month(flow, "2026-08")
    assert july.planned_out == D("200.00")
    assert (july.realized_out, july.projected_out) == (D("0.00"), D("0.00"))
    assert august.projected_out == D("200.00")     # RB-025: vencido e não pago é pendente hoje


def test_partial_payment_projects_only_the_remaining_balance(client, db_session):
    w = make_world(client, "cf8@example.com")
    bill = w.post("/commitments", direction="payable", description="Reforma", amount="1000.00", due_date="2026-09-10", category_id=w.rent)[0]
    w.post(f"/commitments/{bill['id']}/settlements", account_id=w.checking, amount="400.00", paid_at="2026-08-15")

    flow = _flow(db_session, w)

    august, september = _month(flow, "2026-08"), _month(flow, "2026-09")
    assert august.realized_out == D("400.00")
    assert (september.planned_out, september.projected_out) == (D("1000.00"), D("600.00"))


def test_receivable_is_an_inflow(client, db_session):
    w = make_world(client, "cf9@example.com")
    w.post("/commitments", direction="receivable", description="Freela", amount="800.00", due_date="2026-09-15", category_id=w.salary)

    september = _month(_flow(db_session, w), "2026-09")

    assert (september.planned_in, september.projected_in, september.projected_out) == (D("800.00"), D("800.00"), D("0.00"))


def test_canceled_commitment_is_excluded(client, db_session):
    w = make_world(client, "cf10@example.com")
    bill = w.post("/commitments", direction="payable", description="Cancelada", amount="500.00", due_date="2026-09-10", category_id=w.rent)[0]
    w.post(f"/commitments/{bill['id']}/cancel")

    september = _month(_flow(db_session, w), "2026-09")

    assert (september.planned_out, september.projected_out) == (D("0.00"), D("0.00"))


def test_future_dated_transaction_in_a_cash_account_is_planned(client, db_session):
    w = make_world(client, "cf11@example.com")
    w.tx(w.checking, w.rent, "expense", "700.00", "2026-09-05")

    flow = _flow(db_session, w)

    september = _month(flow, "2026-09")
    assert (september.planned_out, september.projected_out, september.realized_out) == (D("700.00"), D("700.00"), D("0.00"))
    assert flow.cash_balance_today == D("1500.00")  # ainda não aconteceu


# ---------- cartão ----------

def test_open_invoice_is_planned_at_its_due_date_and_removed_from_projection_when_paid(client, db_session):
    w = make_world(client, "cf12@example.com")
    w.post(f"/cards/{w.card_id}/purchases", description="TV", amount="600.00", purchase_date="2026-08-10", category_id=w.market)

    unpaid = _month(_flow(db_session, w), "2026-09")        # fecha 05/09, vence 12/09
    assert (unpaid.planned_out, unpaid.projected_out) == (D("600.00"), D("600.00"))

    w.post(f"/cards/{w.card_id}/invoices/2026-09-05/payments", amount="600.00", paid_at="2026-08-18")
    paid = _flow(db_session, w)

    assert _month(paid, "2026-09").projected_out == D("0.00")   # quitada: nada resta
    assert _month(paid, "2026-08").realized_out == D("600.00")  # o dinheiro saiu em agosto, quando foi paga


def test_installments_appear_one_per_invoice_due_month(client, db_session):
    w = make_world(client, "cf13@example.com")
    w.post(f"/cards/{w.card_id}/purchases", description="Notebook", amount="900.00", purchase_date="2026-08-10", category_id=w.market, installments=3)

    flow = _flow(db_session, w)

    assert [_month(flow, m).planned_out for m in ("2026-09", "2026-10", "2026-11")] == [D("300.00")] * 3
    assert _month(flow, "2026-08").planned_out == D("0.00")


def test_card_purchases_are_never_counted_twice(client, db_session):
    """Compra no cartão + fatura: uma única saída, no vencimento (ou no pagamento)."""
    w = make_world(client, "cf14@example.com")
    w.post(f"/cards/{w.card_id}/purchases", description="TV", amount="600.00", purchase_date="2026-08-10", category_id=w.market)

    flow = _flow(db_session, w)

    total_projected_out = sum((m.projected_out for m in flow.months), D("0.00"))
    assert total_projected_out == D("600.00")


# ---------- recorrências expandidas (decisão 4) ----------

def test_monthly_recurrence_is_expanded_into_future_months(client, db_session):
    w = make_world(client, "cf15@example.com")
    w.post("/recurring", account_id=w.checking, category_id=w.rent, type="expense", amount="1200.00",
           frequency="monthly", next_occurrence_date="2026-09-10", description="Aluguel")

    flow = _flow(db_session, w)

    assert [_month(flow, m).projected_out for m in ("2026-09", "2026-10", "2026-11", "2026-12")] == [D("1200.00")] * 4
    assert _month(flow, "2026-08").projected_out == D("0.00")


def test_recurrence_does_not_duplicate_what_was_already_generated(client, db_session):
    """A expansão começa em `next_occurrence_date`; o que já virou compromisso fica de fora dela."""
    w = make_world(client, "cf16@example.com")
    recurring = w.post("/recurring", account_id=w.checking, category_id=w.rent, type="expense", amount="1200.00",
                       frequency="monthly", next_occurrence_date="2026-08-10", generate_as_commitment=True)
    from src.features.recurring import service as recurring_service

    recurring_service.generate_due_commitments(db_session, as_of=date(2026, 8, 20))  # cria 10/08 e 10/09
    assert recurring["id"]

    flow = _flow(db_session, w)

    assert _month(flow, "2026-08").planned_out == D("1200.00")   # só o compromisso, sem a ocorrência virtual
    assert _month(flow, "2026-09").planned_out == D("1200.00")
    assert _month(flow, "2026-10").planned_out == D("1200.00")   # a expansão assume daqui para frente


def test_recurrence_on_a_card_account_lands_on_the_invoice_due_date(client, db_session):
    w = make_world(client, "cf17@example.com")
    w.post("/recurring", account_id=w.card_account, category_id=w.market, type="expense", amount="50.00",
           frequency="monthly", next_occurrence_date="2026-08-25", description="Streaming")

    flow = _flow(db_session, w)

    # compra de 25/08 fecha em 05/09 e vence em 12/09: sai do caixa em setembro, não em agosto
    assert _month(flow, "2026-08").projected_out == D("0.00")
    assert _month(flow, "2026-09").projected_out == D("50.00")


def test_inactive_recurrence_is_not_projected(client, db_session):
    w = make_world(client, "cf18@example.com")
    recurring = w.post("/recurring", account_id=w.checking, category_id=w.rent, type="expense", amount="10.00",
                       frequency="monthly", next_occurrence_date="2026-09-10")
    w.post(f"/recurring/{recurring['id']}/deactivate")

    assert _month(_flow(db_session, w), "2026-09").projected_out == D("0.00")


# ---------- projeção encadeada ----------

def test_projected_balance_accumulates_through_future_months(client, db_session):
    w = make_world(client, "cf19@example.com")  # 1500 em caixa
    w.post("/recurring", account_id=w.checking, category_id=w.salary, type="income", amount="3000.00",
           frequency="monthly", next_occurrence_date="2026-09-05")
    w.post("/recurring", account_id=w.checking, category_id=w.rent, type="expense", amount="1000.00",
           frequency="monthly", next_occurrence_date="2026-09-10")

    flow = _flow(db_session, w)

    assert _month(flow, "2026-08").closing_projected == D("1500.00")
    assert _month(flow, "2026-09").closing_projected == D("3500.00")
    assert _month(flow, "2026-10").opening_balance == D("3500.00")
    assert _month(flow, "2026-10").closing_projected == D("5500.00")


def test_window_starting_in_the_future_still_accounts_for_the_months_before_it(client, db_session):
    w = make_world(client, "cf20@example.com")
    w.post("/recurring", account_id=w.checking, category_id=w.salary, type="income", amount="3000.00",
           frequency="monthly", next_occurrence_date="2026-09-05")

    flow = cash_flow.build_cash_flow(db_session, w.user_id, date(2026, 11, 1), 2, today=TODAY)

    assert flow.months[0].month == "2026-11"
    # 1500 em caixa + 3000 de setembro + 3000 de outubro, antes de a janela (novembro) começar
    assert flow.months[0].opening_balance == D("7500.00")


# ---------- detalhe ----------

def test_items_sum_to_each_column_total(client, db_session):
    """Propriedade: a lista de itens de um número é exatamente o que compõe esse número."""
    w = make_world(client, "cf21@example.com")
    w.tx(w.checking, w.salary, "income", "3000.00", "2026-08-05", "Salário")
    w.tx(w.checking, w.market, "expense", "250.00", "2026-08-09", "Feira")
    w.post("/commitments", direction="payable", description="IPTU", amount="200.00", due_date="2026-07-10", category_id=w.rent)
    w.post("/commitments", direction="payable", description="Seguro", amount="90.00", due_date="2026-08-28", category_id=w.rent)
    w.post("/recurring", account_id=w.checking, category_id=w.rent, type="expense", amount="400.00",
           frequency="weekly", next_occurrence_date="2026-08-24")
    w.post(f"/cards/{w.card_id}/purchases", description="TV", amount="600.00", purchase_date="2026-08-03", category_id=w.market)

    flow = _flow(db_session, w)

    for month in flow.months:
        first = cash_flow.parse_month(month.month)
        for column, expected in (
            ("planned", {"in": month.planned_in, "out": month.planned_out}),
            ("realized", {"in": month.realized_in, "out": month.realized_out}),
            ("projected", {"in": month.projected_in, "out": month.projected_out}),
        ):
            for direction in ("in", "out"):
                items = cash_flow.month_items(db_session, w.user_id, first, column, direction, today=TODAY)
                assert sum((i.amount for i in items), D("0.00")) == expected[direction], (month.month, column, direction)


def test_items_describe_where_each_number_comes_from(client, db_session):
    w = make_world(client, "cf22@example.com")
    w.post("/commitments", direction="payable", description="Seguro", amount="90.00", due_date="2026-08-28", category_id=w.rent)

    items = cash_flow.month_items(db_session, w.user_id, date(2026, 8, 1), "planned", "out", today=TODAY)

    assert [(i.source, i.description, i.category_name, i.amount) for i in items] == [
        ("commitments", "Seguro", "Aluguel", D("90.00"))
    ]


# ---------- isolamento ----------

def test_cash_flow_is_isolated_per_user(client, db_session):
    owner = make_world(client, "cf23owner@example.com")
    other = make_world(client, "cf23other@example.com", checking_opening="0.00", savings_opening="0.00")
    owner.tx(owner.checking, owner.salary, "income", "9999.00", "2026-08-05")
    owner.post("/commitments", direction="payable", description="Dele", amount="500.00", due_date="2026-09-10", category_id=owner.rent)

    flow = _flow(db_session, other)

    assert all(m.realized_in == D("0.00") and m.planned_out == D("0.00") for m in flow.months)
    assert flow.cash_balance_today == D("0.00")
