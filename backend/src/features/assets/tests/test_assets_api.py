"""Bens e avaliações (Marco 12): valor em uma data, vínculo com dívida, baixa e isolamento."""

from datetime import date, timedelta
from decimal import Decimal

from src.features.reports.tests.conftest_helpers import make_world

D = Decimal
TODAY = date.today()


def world(client, email):
    w = make_world(client, email)
    w.interest = w.post("/categories", name="Juros", dre_group="financial_expense")["id"]
    return w


def new_asset(w, **overrides):
    body = dict(name="Carro", kind="vehicle", current_value="30000.00", valued_at=TODAY.isoformat())
    body.update(overrides)
    return w.post("/assets", **body)


def new_debt(w):
    return w.post(
        "/debts",
        name="Financiamento do carro",
        principal="10000.00",
        contracted_at=TODAY.isoformat(),
        installments=24,
        first_due_date=(TODAY + timedelta(days=10)).isoformat(),
        system="price",
        monthly_rate="1",
        interest_category_id=w.interest,
        payment_account_id=w.checking,
        received_account_id=None,
    )


def test_creating_an_asset_records_its_first_valuation(client):
    w = world(client, "a1@example.com")

    asset = new_asset(w, acquired_at="2024-01-10", acquisition_value="35000.00")

    assert asset["value"] == "30000.00"
    assert asset["valued_at"] == TODAY.isoformat()
    assert asset["acquisition_value"] == "35000.00"
    assert [v["value"] for v in asset["valuations"]] == ["30000.00"]


def test_value_is_the_latest_valuation_up_to_the_date_and_zero_before_the_first(client):
    w = world(client, "a2@example.com")
    asset = new_asset(w, valued_at=(TODAY - timedelta(days=60)).isoformat(), current_value="30000.00")
    w.post(f"/assets/{asset['id']}/valuations", value="28000.00", valued_at=(TODAY - timedelta(days=10)).isoformat())

    now = w.get(f"/assets/{asset['id']}").json()
    before = w.get("/reports/net-worth", as_of=(TODAY - timedelta(days=90)).isoformat()).json()
    middle = w.get("/reports/net-worth", as_of=(TODAY - timedelta(days=30)).isoformat()).json()

    assert now["value"] == "28000.00"
    assert before["assets_total"] == "0.00"  # RB-030
    assert middle["assets_total"] == "30000.00"


def test_same_date_valuation_corrects_instead_of_duplicating(client):
    w = world(client, "a3@example.com")
    asset = new_asset(w)

    result = w.post(f"/assets/{asset['id']}/valuations", value="31000.00", valued_at=TODAY.isoformat())

    assert [v["value"] for v in result["valuations"]] == ["31000.00"]


def test_last_valuation_cannot_be_removed(client):
    w = world(client, "a4@example.com")
    asset = new_asset(w)
    only = asset["valuations"][0]["id"]

    refused = client.delete(f"/assets/{asset['id']}/valuations/{only}", headers=w.headers)
    w.post(f"/assets/{asset['id']}/valuations", value="29000.00", valued_at=(TODAY - timedelta(days=5)).isoformat())
    allowed = client.delete(f"/assets/{asset['id']}/valuations/{only}", headers=w.headers)

    assert refused.status_code == 409
    assert allowed.status_code == 200
    assert allowed.json()["value"] == "29000.00"


def test_future_valuation_is_rejected(client):
    w = world(client, "a5@example.com")
    asset = new_asset(w)

    response = client.post(
        f"/assets/{asset['id']}/valuations",
        json={"value": "1.00", "valued_at": (TODAY + timedelta(days=1)).isoformat()},
        headers=w.headers,
    )

    assert response.status_code == 422


def test_a_debt_can_finance_only_one_asset(client):
    w = world(client, "a6@example.com")
    debt = new_debt(w)
    new_asset(w, debt_id=debt["id"])

    response = client.post(
        "/assets",
        json={"name": "Outro", "kind": "other", "current_value": "10.00", "debt_id": debt["id"]},
        headers=w.headers,
    )

    assert response.status_code == 409


def test_unknown_debt_is_rejected(client):
    w = world(client, "a7@example.com")

    response = client.post(
        "/assets",
        json={
            "name": "Casa",
            "kind": "real_estate",
            "current_value": "100.00",
            "debt_id": "00000000-0000-0000-0000-000000000000",
        },
        headers=w.headers,
    )

    assert response.status_code == 404


def test_disposed_asset_is_worth_zero_from_that_date_but_not_before(client):
    w = world(client, "a8@example.com")
    asset = new_asset(w, valued_at=(TODAY - timedelta(days=60)).isoformat())
    sold_on = TODAY - timedelta(days=20)

    w.client.patch(f"/assets/{asset['id']}", json={"disposed_at": sold_on.isoformat()}, headers=w.headers)

    assert w.get(f"/assets/{asset['id']}").json()["value"] == "0.00"
    assert w.get("/reports/net-worth", as_of=(TODAY - timedelta(days=30)).isoformat()).json()["assets_total"] == "30000.00"
    assert w.get("/reports/net-worth").json()["assets_total"] == "0.00"


def test_stale_valuation_is_flagged(client):
    w = world(client, "a9@example.com")
    asset = new_asset(w, valued_at=(TODAY - timedelta(days=400)).isoformat())

    assert w.get(f"/assets/{asset['id']}").json()["is_stale"] is True
    assert any("12 meses" in message for message in w.get("/reports/net-worth").json()["warnings"])


def test_assets_are_isolated_between_users(client):
    a = world(client, "a10a@example.com")
    b = world(client, "a10b@example.com")
    asset = new_asset(a)

    response = client.get(f"/assets/{asset['id']}", headers=b.headers)
    patch = client.patch(f"/assets/{asset['id']}", json={"name": "x"}, headers=b.headers)

    assert response.status_code == 404
    assert patch.status_code == 404
    assert b.get("/assets").json() == []
