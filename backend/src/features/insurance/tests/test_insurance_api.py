"""Apólices (Marco 15): o prêmio entra no fluxo uma vez só e os alertas aparecem."""

from datetime import date, timedelta
from decimal import Decimal

from src.features.reports.tests.conftest_helpers import make_world

D = Decimal
TODAY = date.today()


def world(client, email):
    w = make_world(client, email)
    w.premium = w.post("/categories", name="Seguros", dre_group="fixed_expense")["id"]
    return w


def policy(w, **overrides):
    body = dict(
        kind="auto", insurer="Seguradora X", name="Carro", premium_amount="300.00", premium_frequency="monthly",
        coverage_amount="40000.00", renews_on=(TODAY + timedelta(days=200)).isoformat(),
        first_due_on=(TODAY + timedelta(days=10)).isoformat(), payment_account_id=w.checking,
        category_id=w.premium,
    )
    body.update(overrides)
    return w.post("/insurance", **body)


def test_monthly_policy_creates_a_recurring_that_generates_payables(client):
    w = world(client, "s1@example.com")

    created = policy(w)

    recurring = w.get("/recurring").json()
    assert len(recurring) == 1
    assert recurring[0]["id"] == created["recurring_id"]
    assert recurring[0]["amount"] == "300.00"
    assert recurring[0]["frequency"] == "monthly"
    assert recurring[0]["generate_as_commitment"] is True
    assert created["commitment_id"] is None


def test_annual_policy_creates_a_single_payable_at_the_renewal_date(client):
    w = world(client, "s2@example.com")
    renews = TODAY + timedelta(days=60)

    created = policy(w, premium_frequency="annual", premium_amount="2400.00", renews_on=renews.isoformat())

    items = w.get("/commitments").json()["items"]
    assert len(items) == 1
    assert items[0]["id"] == created["commitment_id"]
    assert items[0]["due_date"] == renews.isoformat()
    assert items[0]["amount"] == "2400.00"
    assert items[0]["description"] == "Seguro Carro"
    assert w.get("/recurring").json() == []  # nada duplicado (R-15.3)


def test_premium_shows_up_in_the_cash_flow_only_once(client):
    w = world(client, "s3@example.com")
    policy(w)
    month = TODAY.strftime("%Y-%m")

    flow = w.get("/reports/cash-flow", start_month=month, months=3).json()

    planned = sum(D(m["planned_out"]) for m in flow["months"])
    assert planned >= D("300.00")
    assert planned <= D("900.00")  # no máximo uma parcela por mês nos 3 meses


def test_changing_the_premium_updates_the_recurring(client):
    w = world(client, "s4@example.com")
    created = policy(w)

    client.patch(f"/insurance/{created['id']}", json={"premium_amount": "350.00"}, headers=w.headers)

    assert w.get("/recurring").json()[0]["amount"] == "350.00"


def test_renewing_an_annual_policy_advances_the_term_and_creates_the_next_premium(client):
    w = world(client, "s5@example.com")
    renews = TODAY + timedelta(days=20)
    created = policy(w, premium_frequency="annual", premium_amount="2400.00", renews_on=renews.isoformat())

    renewed = w.post(f"/insurance/{created['id']}/renew", premium_amount="2600.00")

    assert renewed["renews_on"] == renews.replace(year=renews.year + 1).isoformat()
    items = w.get("/commitments").json()["items"]
    assert sorted(i["amount"] for i in items) == ["2400.00", "2600.00"]


def test_deactivating_stops_the_recurring_and_cancels_the_open_payable(client):
    w = world(client, "s6@example.com")
    monthly = policy(w)
    annual = policy(w, name="Casa", kind="home", premium_frequency="annual",
                    renews_on=(TODAY + timedelta(days=40)).isoformat())

    w.post(f"/insurance/{monthly['id']}/deactivate")
    w.post(f"/insurance/{annual['id']}/deactivate")

    assert w.get("/recurring").json()[0]["is_active"] is False
    [commitment] = w.get("/commitments").json()["items"]
    assert commitment["status"] == "canceled"
    assert client.post(f"/insurance/{annual['id']}/renew", json={}, headers=w.headers).status_code == 409


def test_summary_flags_renewals_overdue_and_uninsured_assets(client):
    w = world(client, "s7@example.com")
    car = w.post("/assets", name="Carro", kind="vehicle", current_value="40000.00")
    house = w.post("/assets", name="Casa", kind="real_estate", current_value="400000.00")
    policy(w, name="Auto", asset_id=car["id"], renews_on=(TODAY + timedelta(days=10)).isoformat())
    policy(w, name="Vida", kind="life", renews_on=(TODAY - timedelta(days=3)).isoformat())

    summary = w.get("/insurance/summary").json()

    assert summary["active_count"] == 2
    assert [p["name"] for p in summary["renewals_soon"]] == ["Auto"]
    assert [p["name"] for p in summary["overdue_renewals"]] == ["Vida"]
    assert [a["name"] for a in summary["uninsured_assets"]] == ["Casa"]
    assert summary["uninsured_assets"][0]["asset_id"] == house["id"]
    assert summary["monthly_cost"] == "600.00"


def test_annual_premium_is_normalized_to_a_monthly_cost(client):
    w = world(client, "s8@example.com")
    policy(w, premium_frequency="annual", premium_amount="1200.00",
           renews_on=(TODAY + timedelta(days=100)).isoformat())

    assert w.get("/insurance/summary").json()["monthly_cost"] == "100.00"


def test_policy_validations_and_isolation(client):
    a = world(client, "s9a@example.com")
    b = world(client, "s9b@example.com")
    created = policy(a)

    bad_account = client.post(
        "/insurance",
        json={"kind": "auto", "insurer": "X", "name": "Y", "premium_amount": "10", "premium_frequency": "monthly",
              "renews_on": TODAY.isoformat(), "payment_account_id": b.checking, "category_id": a.premium},
        headers=a.headers,
    )

    assert bad_account.status_code == 404
    assert client.patch(f"/insurance/{created['id']}", json={"name": "x"}, headers=b.headers).status_code == 404
    assert b.get("/insurance").json() == []
