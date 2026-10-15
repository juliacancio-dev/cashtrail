"""Fontes externas de dados (decisão 2): cotações (brapi) e índices (Banco Central).

Só a biblioteca padrão (urllib), com timeout curto. O restante do sistema depende dos protocolos
`QuoteProvider` e `IndexProvider`, então trocar de fonte não toca regra de negócio e os testes
usam provedores falsos (nenhum teste chama a rede).

SEGURANÇA: o token da brapi só existe no backend (variável de ambiente) e nunca é logado.
"""

import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, timedelta
from decimal import Decimal
from typing import Protocol

from src.core.config import settings

TIMEOUT_SECONDS = 8
BCB_WINDOW_DAYS = 365 * 9  # a API limita a 10 anos por consulta
CDI_DAILY_SERIES = 12


class QuoteError(Exception):
    """A fonte não devolveu um preço utilizável (rede, limite, ativo desconhecido, resposta inesperada)."""


class IndexError_(Exception):
    """A fonte de índices não respondeu."""


class QuoteProvider(Protocol):
    name: str

    def get_price(self, symbol: str) -> Decimal: ...


class IndexProvider(Protocol):
    def cdi_daily(self, start: date, end: date) -> list[tuple[date, Decimal]]:
        """Taxa do CDI por dia, em PERCENTUAL ao dia (0.050788 = 0,050788% a.d.)."""
        ...


def _get_json(url: str, headers: dict[str, str] | None = None):
    request = urllib.request.Request(url, headers={"Accept": "application/json", **(headers or {})})
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:  # noqa: S310 (https fixo)
        return json.loads(response.read().decode("utf-8"))


class BrapiProvider:
    name = "brapi"

    def __init__(self, base_url: str | None = None, token: str | None = None) -> None:
        self.base_url = (base_url or settings.brapi_base_url).rstrip("/")
        self.token = token if token is not None else settings.brapi_token

    def get_price(self, symbol: str) -> Decimal:
        url = f"{self.base_url}/api/quote/{urllib.parse.quote(symbol, safe='')}"
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        try:
            payload = _get_json(url, headers)
            price = payload["results"][0]["regularMarketPrice"]
            value = Decimal(str(price))
        except urllib.error.HTTPError as exc:
            # Sem token, a brapi só atende alguns ativos de teste; 401/402/429 viram erro claro.
            raise QuoteError(f"{symbol}: a fonte respondeu {exc.code}") from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise QuoteError(f"{symbol}: fonte indisponivel") from None
        except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError, ArithmeticError):
            raise QuoteError(f"{symbol}: resposta inesperada da fonte") from None
        if value < 0:
            raise QuoteError(f"{symbol}: preco invalido")
        return value


class BcbProvider:
    """API de dados abertos do Banco Central (SGS): pública, sem autenticação."""

    def cdi_daily(self, start: date, end: date) -> list[tuple[date, Decimal]]:
        result: list[tuple[date, Decimal]] = []
        cursor = start
        while cursor <= end:
            window_end = min(cursor + timedelta(days=BCB_WINDOW_DAYS), end)
            query = urllib.parse.urlencode(
                {"formato": "json", "dataInicial": cursor.strftime("%d/%m/%Y"), "dataFinal": window_end.strftime("%d/%m/%Y")}
            )
            url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{CDI_DAILY_SERIES}/dados?{query}"
            try:
                rows = _get_json(url)
                for row in rows:
                    day, value = row["data"], Decimal(row["valor"])
                    d, m, y = day.split("/")
                    result.append((date(int(y), int(m), int(d)), value))
            except (urllib.error.URLError, TimeoutError, OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
                raise IndexError_("indice indisponivel") from None
            cursor = window_end + timedelta(days=1)
        return result


def get_quote_provider() -> QuoteProvider:
    """Dependência do FastAPI: os testes substituem por um provedor falso."""
    return BrapiProvider()


def get_index_provider() -> IndexProvider:
    return BcbProvider()
