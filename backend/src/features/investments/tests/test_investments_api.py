"""Carteira pela API (Marco 13): compra/venda/provento nunca contam em dobro (RB-033 a RB-037).

Nenhum teste chama a rede: as fontes externas são substituídas por provedores falsos.
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest

from src.features.investments.providers import (
    IndexError_,
    QuoteError,
    get_index_provider,
    get_quote_provider,
)
from src.features.reports.tests.conftest_helpers import make_world
from src.main import app

D = Decimal
TODAY = date.today()
START = TODAY - timedelta(days=40)


class FakeQuotes:
    name = "fake"

    def __init__(self, prices=None, fail=()):
        self.prices = prices or {}
        self.fail = set(fail)
        self.calls: list[str] = []

    def get_price(self, symbol):
        self.calls.append(symbol)
        if symbol in self.fail or symbol not in self.prices:
            raise QuoteError(symbol)
        return D(str(self.prices[symbol]))


class FakeIndex:
    def __init__(self, daily="0.05", fail=False):
        self.daily, self.fail = D(daily), fail

    def cdi_daily(self, start, end):
        if self.fail:
            raise IndexError_("fora do ar")
        days = (end - start).days + 1
        return [(start + timedelta(days=i), self.daily) for i in range(days)]


@pytest.fixture
def providers():
    quotes, index = FakeQuotes(prices={"PETR4": 25, "HGLG11": 160}), FakeIndex()
    app.dependency_overrides[get_quote_provider] = lambda: quotes
    app.dependency_overrides[get_index_provider] = lambda: index
    yield quotes, index
    app.dependency_overrides.pop(get_quote_provider, None)
    app.dependency_overrides.pop(get_index_provider, None)


def world(client, email):
    w = make_world(client, email, checking_opening="10000.00", savings_opening="0.00")
    w.invest_account = w.post("/accounts", name="Corretora", type="investment")["id"]
    w.revenue = w.post("/categories", name="Ganho de capital", dre_group="financial_revenue")["id"]
    w.loss = w.post("/categories", name="Perda de capital", dre_group="financial_expense")["id"]
    return w


def asset(w, **overrides):
    body = dict(account_id=w.invest_account, name="Petrobras PN", symbol="PETR4", asset_class="stock",
                quote_source="brapi")
    body.update(overrides)
    return w.post("/investments/assets", **body)


def buy(w, asset_id, quantity="10", price="20", fees="0", day=None):
    return w.post(
        f"/investments/assets/{asset_id}/operations", kind="buy", occurred_at=(day or START).isoformat(),
        quantity=quantity, unit_price=price, fees=fees, cash_account_id=w.checking,
    )


def balances(w):
    body = w.get("/reports/balances").json()
    return {a["name"]: D(a["balance"]) for a in body["accounts"]}, body


def net(w):
    return w.get("/reports/net-worth").json()


def dre(w):
    return w.get("/reports/dre", start_date=(TODAY - timedelta(days=90)).isoformat(), end_date=TODAY.isoformat()).json()


def test_buying_moves_cash_to_the_investment_account_without_changing_net_worth_or_dre(client, providers):
    w = world(client, "i1@example.com")
    before = D(net(w)["net_worth"])
    a = asset(w)

    detail = buy(w, a["id"], "10", "20", fees="5")

    by_name, body = balances(w)
    assert by_name["Corrente"] == D("9795.00")  # 10000 − (200 + 5)
    assert by_name["Corretora"] == D("205.00")  # custo da carteira
    assert body["cash_total"] == "9795.00"  # a conta de investimento não é caixa
    assert detail["quantity"] == "10.000000"
    assert detail["cost"] == "205.00"
    # RB-032: entra pelo valor de mercado (10 × 20 = 200, preço da compra), nada em dobro. As taxas (5)
    # integram o custo, então aparecem como resultado não realizado negativo e o patrimônio cai 5.
    assert D(net(w)["net_worth"]) == before - D("5.00")
    assert net(w)["investments"][0]["unrealized"] == "-5.00"
    assert dre(w)["net_result"] == "0.00"  # RB-033


def test_net_worth_follows_market_value_not_the_account_balance(client, providers):
    w = world(client, "i2@example.com")
    a = asset(w)
    buy(w, a["id"], "10", "20")  # custo 200
    before = D(net(w)["net_worth"])

    w.post(f"/investments/assets/{a['id']}/quote", price="25", quoted_on=TODAY.isoformat())

    body = net(w)
    assert D(body["net_worth"]) == before + D("50.00")
    assert body["investments_total"] == "250.00"
    assert body["investments"][0]["unrealized"] == "50.00"
    assert dre(w)["net_result"] == "0.00"  # RB-037: valorização não é receita


def test_selling_returns_cost_and_books_the_gain_once(client, providers):
    w = world(client, "i3@example.com")
    a = asset(w)
    buy(w, a["id"], "10", "20")  # custo 200

    detail = w.post(
        f"/investments/assets/{a['id']}/operations", kind="sell", occurred_at=TODAY.isoformat(),
        quantity="5", unit_price="25", cash_account_id=w.checking, category_id=w.revenue,
    )

    sell = detail["operations"][0]
    assert (sell["cost_basis"], sell["gain"], sell["amount"]) == ("100.00", "25.00", "125.00")
    by_name, _ = balances(w)
    assert by_name["Corrente"] == D("9925.00")  # 10000 − 200 + 125
    assert by_name["Corretora"] == D("100.00")  # custo remanescente
    assert dre(w)["net_result"] == "25.00"  # o ganho aparece uma vez, no DRE
    assert detail["realized"] == "25.00"
    assert detail["quantity"] == "5.000000"


def test_loss_on_sale_is_a_financial_expense(client, providers):
    w = world(client, "i4@example.com")
    a = asset(w)
    buy(w, a["id"], "10", "20")

    w.post(
        f"/investments/assets/{a['id']}/operations", kind="sell", occurred_at=TODAY.isoformat(),
        quantity="10", unit_price="15", cash_account_id=w.checking, category_id=w.loss,
    )

    assert dre(w)["net_result"] == "-50.00"
    by_name, _ = balances(w)
    assert by_name["Corrente"] == D("9950.00")
    assert by_name["Corretora"] == D("0.00")


def test_sale_with_gain_requires_a_category(client, providers):
    w = world(client, "i5@example.com")
    a = asset(w)
    buy(w, a["id"], "10", "20")

    response = client.post(
        f"/investments/assets/{a['id']}/operations",
        json={"kind": "sell", "occurred_at": TODAY.isoformat(), "quantity": "5", "unit_price": "25",
              "cash_account_id": w.checking},
        headers=w.headers,
    )

    assert response.status_code == 422


def test_income_is_financial_revenue_and_keeps_the_position(client, providers):
    w = world(client, "i6@example.com")
    a = asset(w)
    buy(w, a["id"], "10", "20")

    detail = w.post(
        f"/investments/assets/{a['id']}/operations", kind="income", occurred_at=TODAY.isoformat(),
        amount="7.00", cash_account_id=w.checking, category_id=w.revenue,
    )

    assert detail["income"] == "7.00"
    assert detail["quantity"] == "10.000000"
    assert detail["cost"] == "200.00"
    assert dre(w)["net_result"] == "7.00"
    assert balances(w)[0]["Corrente"] == D("9807.00")


def test_selling_more_than_owned_is_rejected(client, providers):
    w = world(client, "i7@example.com")
    a = asset(w)
    buy(w, a["id"], "10", "20")

    response = client.post(
        f"/investments/assets/{a['id']}/operations",
        json={"kind": "sell", "occurred_at": TODAY.isoformat(), "quantity": "11", "unit_price": "20",
              "cash_account_id": w.checking, "category_id": w.revenue},
        headers=w.headers,
    )

    assert response.status_code == 422


def test_operations_must_be_chronological(client, providers):
    w = world(client, "i8@example.com")
    a = asset(w)
    buy(w, a["id"], "10", "20", day=TODAY - timedelta(days=5))

    response = client.post(
        f"/investments/assets/{a['id']}/operations",
        json={"kind": "buy", "occurred_at": (TODAY - timedelta(days=10)).isoformat(), "quantity": "1",
              "unit_price": "20", "cash_account_id": w.checking},
        headers=w.headers,
    )

    assert response.status_code == 409


def test_only_the_last_operation_can_be_undone_and_undo_reverts_the_money(client, providers):
    w = world(client, "i9@example.com")
    a = asset(w)
    first = buy(w, a["id"], "10", "20", day=START)
    second = buy(w, a["id"], "5", "22", day=START + timedelta(days=1))
    first_id = first["operations"][0]["id"]
    second_id = second["operations"][0]["id"]

    refused = client.delete(f"/investments/assets/{a['id']}/operations/{first_id}", headers=w.headers)
    allowed = client.delete(f"/investments/assets/{a['id']}/operations/{second_id}", headers=w.headers)

    assert refused.status_code == 409
    assert allowed.status_code == 200
    assert allowed.json()["quantity"] == "10.000000"
    by_name, _ = balances(w)
    assert by_name["Corrente"] == D("9800.00")
    assert by_name["Corretora"] == D("200.00")


def test_refresh_updates_quotes_and_survives_a_failing_symbol(client, providers):
    quotes, _ = providers
    w = world(client, "i10@example.com")
    ok = asset(w)
    bad = asset(w, name="Sem fonte", symbol="XXXX3")
    buy(w, ok["id"], "10", "20")
    buy(w, bad["id"], "2", "10")
    quotes.fail.add("XXXX3")

    result = w.post("/investments/refresh")

    assert result["updated"] == ["PETR4"]
    assert result["failed"] == ["XXXX3"]
    portfolio = w.get("/investments").json()
    petr = next(p for p in portfolio["positions"] if p["symbol"] == "PETR4")
    xxxx = next(p for p in portfolio["positions"] if p["symbol"] == "XXXX3")
    assert petr["price"] == "25.000000" and petr["price_source"] == "brapi"
    assert xxxx["price"] == "10.000000" and xxxx["price_source"] == "trade"  # última cotação conhecida


def test_refresh_stops_at_the_monthly_cap(client, providers, monkeypatch):
    quotes, _ = providers
    from src.core.config import settings

    monkeypatch.setattr(settings, "quotes_monthly_cap", 1)
    w = world(client, "i11@example.com")
    asset(w)
    asset(w, name="FII", symbol="HGLG11", asset_class="fii")

    result = w.post("/investments/refresh")

    assert len(result["updated"]) == 1
    assert len(result["skipped_for_cap"]) == 1
    assert len(quotes.calls) == 1


def test_manual_asset_uses_the_value_the_user_informs(client, providers):
    w = world(client, "i12@example.com")
    cdb = asset(w, name="CDB banco X", symbol=None, asset_class="fixed_income", quote_source="manual")
    w.post(
        f"/investments/assets/{cdb['id']}/operations", kind="buy", occurred_at=START.isoformat(),
        quantity="1", unit_price="5000", cash_account_id=w.checking,
    )

    w.post(f"/investments/assets/{cdb['id']}/quote", price="5120.50", quoted_on=TODAY.isoformat())

    position = w.get("/investments").json()["positions"][0]
    assert position["market_value"] == "5120.50"
    assert position["unrealized"] == "120.50"
    assert position["price_source"] == "manual"


def test_asset_without_any_quote_is_valued_at_cost_with_a_warning(client, providers):
    w = world(client, "i13@example.com")
    a = asset(w, name="Sem preço", symbol="ZZZZ3", quote_source="manual")
    # compra grava a cotação "trade"; ajuste não: o ativo abaixo nunca recebeu preço
    w.post(f"/investments/assets/{a['id']}/operations", kind="adjust", occurred_at=START.isoformat(), quantity="3")

    body = w.get("/investments").json()
    assert body["positions"][0]["has_quote"] is False


def test_benchmark_compares_with_cdi_and_tolerates_the_index_being_down(client, providers):
    _, index = providers
    w = world(client, "i14@example.com")
    a = asset(w)
    buy(w, a["id"], "10", "20")
    w.post(f"/investments/assets/{a['id']}/quote", price="25", quoted_on=TODAY.isoformat())

    body = w.get("/investments/benchmark").json()
    assert body["portfolio_return_pct"] == "25.00"
    assert D(body["cdi_return_pct"]) > 0
    assert body["difference_pct"] is not None

    index.fail = True
    down = w.get("/investments/benchmark").json()
    assert down["portfolio_return_pct"] == "25.00"
    assert down["cdi_return_pct"] is None
    assert "CDI" in down["note"]


def test_history_uses_the_quotes_known_at_each_date(client, providers):
    w = world(client, "i15@example.com")
    a = asset(w)
    buy(w, a["id"], "10", "20", day=START)
    w.post(f"/investments/assets/{a['id']}/quote", price="30", quoted_on=(TODAY - timedelta(days=5)).isoformat())

    old = w.get("/reports/net-worth", as_of=(START + timedelta(days=1)).isoformat()).json()
    now = w.get("/reports/net-worth").json()

    assert old["investments_total"] == "200.00"  # cotação "trade" da compra
    assert now["investments_total"] == "300.00"


def test_investments_are_isolated_between_users(client, providers):
    a = world(client, "i16a@example.com")
    b = world(client, "i16b@example.com")
    owned = asset(a)

    assert client.get(f"/investments/assets/{owned['id']}", headers=b.headers).status_code == 404
    assert b.get("/investments").json()["positions"] == []


def test_cannot_register_assets_in_a_non_investment_account(client, providers):
    w = world(client, "i17@example.com")

    response = client.post(
        "/investments/assets",
        json={"account_id": w.checking, "name": "X", "symbol": "X1", "asset_class": "stock",
              "quote_source": "brapi"},
        headers=w.headers,
    )

    assert response.status_code == 404


def test_scheduled_refresh_skips_fresh_quotes_but_the_button_does_not(client, providers, db_session):
    from src.features.investments import service as investments_service

    quotes, _ = providers
    w = world(client, "i18@example.com")
    a = asset(w)
    buy(w, a["id"], "10", "20")
    w.post("/investments/refresh")  # primeira cotação do dia (botão)
    calls_after_button = len(quotes.calls)

    scheduled = investments_service.refresh_all_users(db_session, quotes)
    forced = w.post("/investments/refresh")

    assert scheduled == 0  # cotação com minutos de vida: o job não repete a requisição
    assert len(quotes.calls) == calls_after_button + 1  # só o botão consultou de novo
    assert forced["updated"] == ["PETR4"]
