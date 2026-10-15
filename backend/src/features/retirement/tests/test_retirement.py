"""Independência financeira (Marco 15): fórmulas conferidas à mão, propriedades e API."""

from datetime import date, timedelta
from decimal import Decimal

import pytest

from src.features.investments.providers import IndexError_, get_index_provider
from src.features.reports.tests.conftest_helpers import make_world
from src.features.retirement import calc
from src.main import app

D = Decimal
TODAY = date.today()


# ---------- cálculo puro ----------

@pytest.mark.parametrize(
    ("wanted", "benefit", "rate", "expected"),
    [
        ("5000", "1000", "0.04", "1200000.00"),  # 4.000 × 12 ÷ 4%
        ("3000", "0", "0.035", "1028571.43"),  # 36.000 ÷ 3,5%
        ("2000", "2500", "0.04", "0.00"),  # benefício cobre a renda desejada
    ],
)
def test_target_wealth(wanted, benefit, rate, expected):
    assert calc.target_wealth(D(wanted), D(benefit), D(rate)) == D(expected)


def test_months_to_target_without_return_is_a_plain_division():
    assert calc.months_to_target(D("0"), D("120000"), D("0"), D("1000")) == 120


def test_already_at_target_needs_zero_months():
    assert calc.months_to_target(D("500000"), D("400000"), D("0.04"), D("0")) == 0


def test_unreachable_target_returns_none():
    assert calc.months_to_target(D("1000"), D("1000000"), D("0"), D("0")) is None


def test_required_contribution_without_return():
    assert calc.required_contribution(D("0"), D("120000"), D("0"), 120) == D("1000.00")
    assert calc.required_contribution(D("200000"), D("120000"), D("0.04"), 120) == D("0.00")


@pytest.mark.parametrize("current", ["0", "50000", "250000"])
@pytest.mark.parametrize("annual", ["0", "0.03", "0.06"])
@pytest.mark.parametrize("months", [60, 180, 360])
def test_required_contribution_reaches_the_target_exactly_in_time(current, annual, months):
    target = D("1000000")
    contribution = calc.required_contribution(D(current), target, D(annual), months)

    reached = calc.months_to_target(D(current), target, D(annual), contribution)

    assert reached is not None and reached <= months  # o aporte calculado basta no prazo


def test_more_contribution_never_takes_longer():
    slow = calc.months_to_target(D("10000"), D("500000"), D("0.04"), D("1000"))
    fast = calc.months_to_target(D("10000"), D("500000"), D("0.04"), D("2000"))

    assert fast < slow


def test_higher_return_never_takes_longer():
    low = calc.months_to_target(D("10000"), D("500000"), D("0.02"), D("1500"))
    high = calc.months_to_target(D("10000"), D("500000"), D("0.06"), D("1500"))

    assert high < low


def test_evaluate_reports_progress_scenarios_and_sustainable_income():
    result = calc.evaluate(
        current_age=35, target_age=55, income_wanted=D("5000"), public_benefit=D("1000"),
        annual_return=D("0.04"), withdrawal_rate=D("0.04"), monthly_contribution=D("2000"),
        current_wealth=D("300000"),
    )

    assert result.target == D("1200000.00")
    assert result.progress_pct == D("25.00")
    assert result.sustainable_income_today == D("2000.00")  # 300.000 × 4% ÷ 12 + 1.000
    assert len(result.scenarios) == 9  # 3 taxas × 3 retornos
    assert sum(1 for s in result.scenarios if s.is_base) == 1
    assert result.gap == D("900000.00")


# ---------- API ----------

class FakeIndex:
    def __init__(self, monthly="0.5", fail=False):
        self.monthly, self.fail = D(monthly), fail

    def cdi_daily(self, start, end):
        return []

    def ipca_monthly(self, start, end):
        if self.fail:
            raise IndexError_("fora do ar")
        return [(TODAY - timedelta(days=30 * i), self.monthly) for i in range(14)]


@pytest.fixture
def index():
    fake = FakeIndex()
    app.dependency_overrides[get_index_provider] = lambda: fake
    yield fake
    app.dependency_overrides.pop(get_index_provider, None)


def plan_body(**overrides):
    body = dict(current_age=35, target_age=55, monthly_income_wanted="5000.00", public_benefit_monthly="1000.00",
                real_return_annual="0.04", withdrawal_rate="0.04", monthly_contribution="2000.00",
                include_assets=False)
    body.update(overrides)
    return body


def test_overview_without_a_plan_still_shows_the_invested_wealth(client, index):
    w = make_world(client, "r1@example.com")

    body = w.get("/retirement").json()

    assert body["plan"] is None and body["result"] is None
    assert body["defaults"]["withdrawal_rate"] == "0.04"
    assert body["disclaimer"].startswith("Simulação")


def test_plan_uses_the_market_value_of_the_investments(client, index):
    w = make_world(client, "r2@example.com", checking_opening="500000.00")
    corretora = w.post("/accounts", name="Corretora", type="investment")["id"]
    asset = w.post("/investments/assets", account_id=corretora, name="CDB", asset_class="fixed_income",
                   quote_source="manual")
    w.post(f"/investments/assets/{asset['id']}/operations", kind="buy",
           occurred_at=(TODAY - timedelta(days=5)).isoformat(), quantity="1", unit_price="300000",
           cash_account_id=w.checking)

    body = client.put("/retirement", json=plan_body(), headers=w.headers).json()

    assert body["invested_wealth"] == "300000.00"
    assert body["counted_wealth"] == "300000.00"  # caixa e bens ficam de fora por padrão (RB-047)
    assert body["result"]["target"] == "1200000.00"
    assert body["result"]["progress_pct"] == "25.00"
    assert body["result"]["reaches_by_target_age"] in (True, False)
    assert D(body["ipca_12m_pct"]) > 0  # contexto do Banco Central


def test_include_assets_adds_owned_assets_to_the_counted_wealth(client, index):
    w = make_world(client, "r3@example.com")
    w.post("/assets", name="Apartamento", kind="real_estate", current_value="400000.00")

    without = client.put("/retirement", json=plan_body(), headers=w.headers).json()
    with_assets = client.put("/retirement", json=plan_body(include_assets=True), headers=w.headers).json()

    assert without["counted_wealth"] == "0.00"
    assert with_assets["counted_wealth"] == "400000.00"


def test_target_age_must_be_greater_than_the_current_age(client, index):
    w = make_world(client, "r4@example.com")

    response = client.put("/retirement", json=plan_body(target_age=35), headers=w.headers)

    assert response.status_code == 422


def test_aggressive_assumptions_are_flagged(client, index):
    w = make_world(client, "r5@example.com")

    body = client.put(
        "/retirement", json=plan_body(withdrawal_rate="0.06", real_return_annual="0.09"), headers=w.headers
    ).json()

    assert any("Taxa de retirada acima de 5%" in message for message in body["warnings"])
    assert any("Retorno real acima de 7%" in message for message in body["warnings"])


def test_overview_survives_the_index_provider_being_down(client, index):
    w = make_world(client, "r6@example.com")
    index.fail = True

    body = client.put("/retirement", json=plan_body(), headers=w.headers).json()

    assert body["ipca_12m_pct"] is None
    assert body["result"] is not None


def test_plan_is_isolated_between_users(client, index):
    a = make_world(client, "r7a@example.com")
    b = make_world(client, "r7b@example.com")
    client.put("/retirement", json=plan_body(), headers=a.headers)

    assert b.get("/retirement").json()["plan"] is None
