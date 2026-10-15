"""Provedores externos (decisão 2) com a rede substituída: erros viram QuoteError/IndexError_,
o token nunca aparece em mensagem de erro e a janela de 10 anos do BCB é respeitada."""

import urllib.error
from datetime import date
from decimal import Decimal

import pytest

from src.features.investments import providers
from src.features.investments.providers import BcbProvider, BrapiProvider, IndexError_, QuoteError

SECRET = "tok_super_secreto_123"


def test_brapi_parses_the_regular_market_price(monkeypatch):
    seen = {}

    def fake(url, headers=None):
        seen["url"], seen["headers"] = url, headers
        return {"results": [{"symbol": "PETR4", "regularMarketPrice": 58.02}]}

    monkeypatch.setattr(providers, "_get_json", fake)

    price = BrapiProvider(base_url="https://example.test", token=SECRET).get_price("PETR4")

    assert price == Decimal("58.02")
    assert seen["url"] == "https://example.test/api/quote/PETR4"
    assert seen["headers"] == {"Authorization": f"Bearer {SECRET}"}


def test_brapi_sends_no_authorization_header_without_a_token(monkeypatch):
    seen = {}
    monkeypatch.setattr(
        providers, "_get_json", lambda url, headers=None: seen.update(h=headers) or {"results": [{"regularMarketPrice": 1}]}
    )

    BrapiProvider(base_url="https://example.test", token="").get_price("VALE3")

    assert seen["h"] == {}


@pytest.mark.parametrize("payload", [{}, {"results": []}, {"results": [{"regularMarketPrice": None}]}, {"results": [{}]}])
def test_brapi_unexpected_payloads_become_quote_error(monkeypatch, payload):
    monkeypatch.setattr(providers, "_get_json", lambda url, headers=None: payload)

    with pytest.raises(QuoteError):
        BrapiProvider(base_url="https://example.test", token="").get_price("PETR4")


def test_brapi_http_and_network_failures_become_quote_error_without_leaking_the_token(monkeypatch):
    def http_error(url, headers=None):
        raise urllib.error.HTTPError(url, 401, "Unauthorized", {}, None)

    def network_error(url, headers=None):
        raise urllib.error.URLError("sem rede")

    for failing in (http_error, network_error):
        monkeypatch.setattr(providers, "_get_json", failing)
        with pytest.raises(QuoteError) as caught:
            BrapiProvider(base_url="https://example.test", token=SECRET).get_price("PETR4")
        assert SECRET not in str(caught.value)


def test_symbol_is_url_encoded(monkeypatch):
    seen = {}
    monkeypatch.setattr(
        providers, "_get_json", lambda url, headers=None: seen.update(url=url) or {"results": [{"regularMarketPrice": 1}]}
    )

    BrapiProvider(base_url="https://example.test", token="").get_price("../admin?x=1")

    assert "/api/quote/..%2Fadmin%3Fx%3D1" in seen["url"]


def test_bcb_splits_long_ranges_into_windows_under_ten_years(monkeypatch):
    urls = []

    def fake(url, headers=None):
        urls.append(url)
        return [{"data": "02/01/2020", "valor": "0.05"}]

    monkeypatch.setattr(providers, "_get_json", fake)

    rows = BcbProvider().cdi_daily(date(2005, 1, 1), date(2026, 1, 1))

    assert len(urls) >= 3  # 21 anos → pelo menos 3 janelas
    assert all("sgs.12" in url for url in urls)
    assert rows[0] == (date(2020, 1, 2), Decimal("0.05"))


def test_bcb_failure_becomes_index_error(monkeypatch):
    def boom(url, headers=None):
        raise urllib.error.URLError("fora do ar")

    monkeypatch.setattr(providers, "_get_json", boom)

    with pytest.raises(IndexError_):
        BcbProvider().cdi_daily(date(2026, 1, 1), date(2026, 2, 1))
