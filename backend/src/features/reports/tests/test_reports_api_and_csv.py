"""API de reports (validação, autenticação) e exportação CSV com proteção contra injeção de fórmula."""

from datetime import date
from decimal import Decimal

import pytest

from src.features.reports import csv_export

from .conftest_helpers import make_world

TODAY_REAL = date.today()


# ---------- csv_export (funções puras) ----------

@pytest.mark.parametrize(
    "value",
    ["=1+1", "=HYPERLINK(\"http://evil\",\"x\")", "+cmd|' /C calc'!A0", "-2+3", "@SUM(A1)", "\tTAB", "\rCR"],
)
def test_safe_text_neutralizes_formula_prefixes(value):
    assert csv_export.safe_text(value) == "'" + value


@pytest.mark.parametrize("value", ["Mercado", "Aluguel 2026", "a=b", "R$ 10", "", None])
def test_safe_text_leaves_normal_text_alone(value):
    assert csv_export.safe_text(value) == (value or "")


def test_numbers_use_decimal_comma_and_keep_the_minus_sign():
    assert csv_export.number(Decimal("1234.5")) == "1234,50"
    assert csv_export.number(Decimal("-80.00")) == "-80,00"   # número, não texto: não leva apóstrofo
    assert csv_export.number(None) == ""


# ---------- endpoints ----------

def test_balances_endpoint_shape(client):
    w = make_world(client, "ra1@example.com")

    body = w.get("/reports/balances").json()

    assert {a["name"] for a in body["accounts"]} == {"Corrente", "Poupança", "Cartão"}
    assert (body["cash_total"], body["card_debt_total"]) == ("1500.00", "0.00")


def test_dre_endpoint_defaults_to_the_current_month(client):
    w = make_world(client, "ra2@example.com")
    w.tx(w.checking, w.salary, "income", "1000.00", TODAY_REAL.isoformat())

    body = w.get("/reports/dre").json()

    assert body["start_date"] == TODAY_REAL.replace(day=1).isoformat()
    assert body["net_result"] == "1000.00"
    assert [line["key"] for line in body["lines"]][0] == "revenue"
    assert body["lines"][-1]["key"] == "net_result"


def test_dre_validates_the_period(client):
    w = make_world(client, "ra3@example.com")

    inverted = client.get("/reports/dre", params={"start_date": "2026-08-31", "end_date": "2026-08-01"}, headers=w.headers)
    too_long = client.get("/reports/dre", params={"start_date": "2015-01-01", "end_date": "2026-01-01"}, headers=w.headers)

    assert (inverted.status_code, too_long.status_code) == (422, 422)


def test_cash_flow_endpoint_shape_and_validation(client):
    w = make_world(client, "ra4@example.com")

    ok = w.get("/reports/cash-flow", months=3).json()
    assert len(ok["months"]) == 3
    assert ok["warnings"]

    for params in ({"months": 0}, {"months": 25}, {"start_month": "2026-13"}, {"start_month": "outubro"}):
        assert client.get("/reports/cash-flow", params=params, headers=w.headers).status_code == 422, params


def test_cash_flow_items_endpoint_validates_the_enums(client):
    w = make_world(client, "ra5@example.com")
    base = {"month": "2026-08", "column": "planned", "direction": "out"}

    assert client.get("/reports/cash-flow/items", params=base, headers=w.headers).status_code == 200
    assert client.get("/reports/cash-flow/items", params={**base, "column": "x"}, headers=w.headers).status_code == 422
    assert client.get("/reports/cash-flow/items", params={**base, "direction": "x"}, headers=w.headers).status_code == 422
    assert client.get("/reports/cash-flow/items", params={**base, "month": "2026-99"}, headers=w.headers).status_code == 422


def test_reports_require_authentication(client):
    for path in ("/reports/balances", "/reports/dre", "/reports/dre.csv", "/reports/cash-flow", "/reports/cash-flow.csv"):
        assert client.get(path).status_code == 401, path


def test_reports_are_isolated_per_user_through_the_api(client):
    owner = make_world(client, "ra6owner@example.com")
    other = make_world(client, "ra6other@example.com", checking_opening="0.00", savings_opening="0.00")
    owner.tx(owner.checking, owner.salary, "income", "9999.00", TODAY_REAL.isoformat())

    assert other.get("/reports/dre").json()["net_result"] == "0.00"
    assert other.get("/reports/balances").json()["cash_total"] == "0.00"


# ---------- CSV via API ----------

def test_dre_csv_is_an_attachment_with_bom_and_semicolon_and_decimal_comma(client):
    w = make_world(client, "rc1@example.com")
    w.tx(w.checking, w.salary, "income", "1234.50", TODAY_REAL.isoformat())

    response = client.get("/reports/dre.csv", headers=w.headers)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment" in response.headers["content-disposition"]
    text = response.content.decode("utf-8")
    assert text.startswith("﻿")
    assert "Receitas;;1234,50;" in text
    assert "\r\n" in text


def test_dre_csv_neutralizes_formulas_coming_from_category_names(client):
    w = make_world(client, "rc2@example.com")
    evil = w.post("/categories", name='=HYPERLINK("http://evil.example","clique")', dre_group="revenue")["id"]
    w.tx(w.checking, evil, "income", "10.00", TODAY_REAL.isoformat())

    text = client.get("/reports/dre.csv", headers=w.headers).content.decode("utf-8")

    assert "'=HYPERLINK" in text
    # Nenhuma CÉLULA pode começar com um caractere de fórmula (nem com espaços antes dele).
    cells = [cell.strip('"') for line in text.lstrip("﻿").splitlines() for cell in line.split(";")]
    assert not any(cell.lstrip().startswith(("=", "+", "@")) for cell in cells)
    assert "'=HYPERLINK" in "".join(cells)


def test_negative_amounts_in_csv_are_numbers_not_neutralized_text(client):
    w = make_world(client, "rc3@example.com")
    w.tx(w.checking, w.market, "expense", "80.00", TODAY_REAL.isoformat())

    text = client.get("/reports/dre.csv", headers=w.headers).content.decode("utf-8")

    result_line = next(line for line in text.splitlines() if line.startswith("Resultado do período"))
    assert result_line.split(";")[2] == "-80,00"


def test_cash_flow_csv_has_one_row_per_month(client):
    w = make_world(client, "rc4@example.com")

    response = client.get("/reports/cash-flow.csv", params={"start_month": "2026-08", "months": 3}, headers=w.headers)

    lines = response.content.decode("utf-8").strip().splitlines()
    assert len(lines) == 1 + 3
    assert lines[0].lstrip("﻿").startswith("Mês;Situação;Saldo inicial")
    assert [row.split(";")[0] for row in lines[1:]] == ["2026-08", "2026-09", "2026-10"]
