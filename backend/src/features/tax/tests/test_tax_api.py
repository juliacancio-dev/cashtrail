"""Dossiê do IRPF pela API (Marco 14): informes + despesas marcadas + carteira + bens/dívidas em 31/12."""

from decimal import Decimal

from src.features.reports.tests.conftest_helpers import make_world

D = Decimal
YEAR = 2026


def world(client, email):
    w = make_world(client, email, checking_opening="100000.00", savings_opening="0.00")
    w.invest_account = w.post("/accounts", name="Corretora", type="investment")["id"]
    w.gain_category = w.post("/categories", name="Ganho de capital", dre_group="financial_revenue")["id"]
    w.health = w.post("/categories", name="Plano de saúde")["id"]
    w.education = w.post("/categories", name="Faculdade")["id"]
    for category, kind in ((w.health, "deduction_health"), (w.education, "deduction_education")):
        response = client.patch(f"/categories/{category}", json={"ir_kind": kind}, headers=w.headers)
        assert response.status_code == 200, response.text
    return w


def statement(w, **overrides):
    body = dict(payer_name="Empresa X", kind="salary", gross_income="100000.00", social_security="8000.00",
                withheld_tax="12000.00")
    body.update(overrides)
    return w.post(f"/tax/{YEAR}/statements", **body)


def dossier(w, year=YEAR):
    return w.get(f"/tax/{year}").json()


def test_years_endpoint_lists_the_supported_years(client):
    w = world(client, "t1@example.com")

    body = w.get("/tax/years").json()

    assert YEAR in body["years"]


def test_dossier_for_a_year_without_parameters_is_an_explicit_422(client):
    w = world(client, "t2@example.com")

    response = client.get("/tax/2024", headers=w.headers)

    assert response.status_code == 422
    assert "parametros fiscais" in response.json()["detail"]


def test_future_year_is_rejected(client):
    w = world(client, "t3@example.com")

    assert client.get("/tax/2099", headers=w.headers).status_code == 422


def test_estimate_uses_statements_and_tagged_expenses(client):
    w = world(client, "t4@example.com")
    statement(w)
    w.tx(w.checking, w.health, "expense", "4000.00", f"{YEAR}-05-10")
    w.tx(w.checking, w.education, "expense", "5000.00", f"{YEAR}-06-10")

    body = dossier(w)
    estimate = body["estimate"]

    assert estimate["taxable_income"] == "100000.00"
    assert estimate["health"] == "4000.00"
    assert estimate["education_declared"] == "5000.00"
    assert estimate["education_deducted"] == "3561.50"  # limite por pessoa
    assert estimate["complete"]["tax_due"] == "12315.93"
    assert estimate["simplified"]["tax_due"] == "11744.34"
    assert estimate["best"] == "simplificada"
    assert estimate["simplified"]["balance"] == "-255.66"  # a restituir (IRRF 12.000 já retido)
    assert body["disclaimer"].startswith("Estimativa")
    assert body["parameters"]["unverified"]  # as premissas não verificadas aparecem
    assert body["parameters"]["sources"][0]["url"].startswith("https://www.gov.br/receitafederal")


def test_expenses_outside_the_year_and_untagged_ones_do_not_deduct(client):
    w = world(client, "t5@example.com")
    statement(w)
    w.tx(w.checking, w.health, "expense", "1000.00", f"{YEAR - 1}-12-31")
    w.tx(w.checking, w.market, "expense", "9000.00", f"{YEAR}-03-01")  # sem marca fiscal

    body = dossier(w)

    assert body["estimate"]["health"] == "0.00"
    assert body["untagged_expense_categories"] == 1


def test_dependents_change_the_estimate(client):
    w = world(client, "t6@example.com")
    statement(w)
    before = dossier(w)["estimate"]["complete"]["tax_due"]

    updated = client.put(f"/tax/{YEAR}/dependents", json={"count": 2}, headers=w.headers).json()

    assert updated["dependents"] == 2
    assert updated["estimate"]["dependents_deduction"] == "4550.16"
    assert D(updated["estimate"]["complete"]["tax_due"]) < D(before)


def test_statement_kinds_are_separated_and_exclusive_income_stays_out_of_the_base(client):
    w = world(client, "t7@example.com")
    statement(w)
    statement(w, kind="thirteenth", payer_name="Empresa X", gross_income="8000.00", social_security="0",
              withheld_tax="900.00")
    statement(w, kind="exclusive_other", payer_name="Banco Y", gross_income="1500.00", social_security="0",
              withheld_tax="300.00")
    statement(w, kind="exempt", payer_name="Banco Y (LCI)", gross_income="700.00", social_security="0",
              withheld_tax="0")

    body = dossier(w)

    assert body["estimate"]["taxable_income"] == "100000.00"  # só o salário entra na base
    assert body["estimate"]["withheld_tax"] == "12000.00"  # IRRF exclusivo não compensa no ajuste anual
    assert body["totals_by_kind"]["thirteenth"]["gross"] == "8000.00"
    assert body["totals_by_kind"]["exclusive_other"]["withheld"] == "300.00"
    assert body["totals_by_kind"]["exempt"]["gross"] == "700.00"


def test_deleting_a_statement_updates_the_dossier_and_is_isolated_per_user(client):
    a = world(client, "t8a@example.com")
    b = world(client, "t8b@example.com")
    created = statement(a)["statements"][0]

    other = client.delete(f"/tax/{YEAR}/statements/{created['id']}", headers=b.headers)
    mine = client.delete(f"/tax/{YEAR}/statements/{created['id']}", headers=a.headers)

    assert other.status_code == 404
    assert mine.status_code == 200
    assert mine.json()["statements"] == []
    assert dossier(b)["statements"] == []


def test_variable_income_month_with_sales_above_the_limit_generates_a_darf(client):
    w = world(client, "t9@example.com")
    asset = w.post(
        "/investments/assets", account_id=w.invest_account, name="Petrobras PN", symbol="PETR4",
        asset_class="stock", quote_source="manual",
    )
    w.post(
        f"/investments/assets/{asset['id']}/operations", kind="buy", occurred_at=f"{YEAR}-02-02",
        quantity="1000", unit_price="20", cash_account_id=w.checking,
    )
    w.post(
        f"/investments/assets/{asset['id']}/operations", kind="sell", occurred_at=f"{YEAR}-03-10",
        quantity="1000", unit_price="30", cash_account_id=w.checking, category_id=w.gain_category,
    )

    body = dossier(w)
    [month] = body["variable_income"]

    assert month["month"] == f"{YEAR}-03"
    assert month["modality"] == "stock"
    assert month["sales"] == "30000.00"
    assert month["exempt"] is False
    assert month["tax"] == "1500.00"
    assert month["irrf"] == "1.50"
    assert month["darf_amount"] == "1498.50"
    assert month["due_date"] == f"{YEAR}-04-30"
    assert body["parameters"]["darf_code"] == "6015"


def test_same_day_buy_and_sell_is_flagged_and_not_calculated(client):
    w = world(client, "t10@example.com")
    asset = w.post(
        "/investments/assets", account_id=w.invest_account, name="Vale ON", symbol="VALE3",
        asset_class="stock", quote_source="manual",
    )
    w.post(
        f"/investments/assets/{asset['id']}/operations", kind="buy", occurred_at=f"{YEAR}-04-02",
        quantity="100", unit_price="50", cash_account_id=w.checking,
    )
    w.post(
        f"/investments/assets/{asset['id']}/operations", kind="sell", occurred_at=f"{YEAR}-04-02",
        quantity="100", unit_price="55", cash_account_id=w.checking, category_id=w.gain_category,
    )

    body = dossier(w)

    assert body["variable_income"] == []
    assert any("day trade" in flag for flag in body["day_trade_flags"])


def test_assets_rights_and_debts_use_cost_not_market_value(client):
    w = world(client, "t11@example.com")
    asset = w.post(
        "/investments/assets", account_id=w.invest_account, name="Petrobras PN", symbol="PETR4",
        asset_class="stock", quote_source="manual",
    )
    w.post(
        f"/investments/assets/{asset['id']}/operations", kind="buy", occurred_at=f"{YEAR}-02-02",
        quantity="10", unit_price="20", cash_account_id=w.checking,
    )
    w.post(f"/investments/assets/{asset['id']}/quote", price="40", quoted_on=f"{YEAR}-03-01")
    w.post("/assets", name="Carro", kind="vehicle", current_value="50000.00", valued_at=f"{YEAR}-01-10",
           acquisition_value="45000.00")
    w.post("/assets", name="Sem custo", kind="other", current_value="100.00", valued_at=f"{YEAR}-01-10")

    body = dossier(w)
    rights = {(r["group"], r["name"]): r for r in body["assets_and_rights"]}

    assert rights[("Investimentos", "Petrobras PN")]["amount"] == "200.00"  # custo, não 400 de mercado
    assert rights[("Bens", "Carro")]["amount"] == "45000.00"  # aquisição, não 50.000 de avaliação
    assert rights[("Bens", "Sem custo")]["note"].startswith("sem valor de aquisição")
    assert any("sem valor de aquisição" in w_ for w_ in body["warnings"])


def test_csv_export_has_bom_disclaimer_and_neutralizes_formula_names(client):
    w = world(client, "t12@example.com")
    statement(w, payer_name="=HYPERLINK(\"http://evil\")")

    response = client.get(f"/tax/{YEAR}/export.csv", headers=w.headers)

    text = response.content.decode("utf-8")
    assert response.status_code == 200
    assert text.startswith("﻿")
    assert "'=HYPERLINK" in text
    assert "não substitui um contador" in text
    assert "Mais vantajosa" in text
