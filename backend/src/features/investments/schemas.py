import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

AssetClass = Literal["stock", "fii", "etf", "bdr", "fixed_income", "treasury", "fund", "crypto", "other"]
QuoteSource = Literal["brapi", "manual"]
OperationKind = Literal["buy", "sell", "income", "adjust"]


class AssetCreate(BaseModel):
    account_id: uuid.UUID
    name: str = Field(min_length=1, max_length=120)
    symbol: str | None = Field(default=None, max_length=20)
    asset_class: AssetClass
    quote_source: QuoteSource = "manual"


class AssetUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    symbol: str | None = Field(default=None, max_length=20)
    quote_source: QuoteSource | None = None
    is_archived: bool | None = None

    @model_validator(mode="after")
    def _no_nulls_for_required(self) -> "AssetUpdate":
        for field in ("name", "quote_source", "is_archived"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} nao pode ser removido")
        return self


class OperationCreate(BaseModel):
    kind: OperationKind
    occurred_at: date
    # Compra/venda: quantidade e preço unitário. Ajuste: quantidade (pode ser negativa).
    quantity: Decimal = Field(default=Decimal("0"), max_digits=18, decimal_places=6)
    unit_price: Decimal = Field(default=Decimal("0"), ge=0, max_digits=14, decimal_places=6)
    fees: Decimal = Field(default=Decimal("0"), ge=0, max_digits=12, decimal_places=2)
    # Só provento: valor recebido.
    amount: Decimal = Field(default=Decimal("0"), ge=0, max_digits=14, decimal_places=2)
    cash_account_id: uuid.UUID | None = None
    category_id: uuid.UUID | None = None
    note: str | None = Field(default=None, max_length=255)


class OperationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    kind: OperationKind
    occurred_at: date
    quantity: Decimal
    unit_price: Decimal
    fees: Decimal
    amount: Decimal
    cost_basis: Decimal | None
    gain: Decimal | None
    cash_account_id: uuid.UUID | None
    category_id: uuid.UUID | None
    note: str | None
    created_at: datetime


class QuoteCreate(BaseModel):
    price: Decimal = Field(ge=0, max_digits=14, decimal_places=6)
    quoted_on: date | None = None


class PositionRead(BaseModel):
    id: uuid.UUID
    account_id: uuid.UUID
    name: str
    symbol: str | None
    asset_class: AssetClass
    quote_source: QuoteSource
    is_archived: bool
    quantity: Decimal
    avg_cost: Decimal
    cost: Decimal
    price: Decimal | None
    price_date: date | None
    price_source: str | None
    market_value: Decimal
    has_quote: bool
    is_stale_quote: bool
    unrealized: Decimal
    unrealized_pct: Decimal | None
    invested: Decimal
    proceeds: Decimal
    income: Decimal
    realized: Decimal
    total_return: Decimal
    total_return_pct: Decimal | None
    first_buy: date | None


class PositionDetail(PositionRead):
    operations: list[OperationRead]


class PortfolioTotals(BaseModel):
    market_value: Decimal
    cost: Decimal
    unrealized: Decimal
    invested: Decimal
    income: Decimal
    realized: Decimal
    total_return: Decimal
    total_return_pct: Decimal | None


class Portfolio(BaseModel):
    positions: list[PositionRead]
    totals: PortfolioTotals
    warnings: list[str]


class RefreshRead(BaseModel):
    updated: list[str]
    failed: list[str]
    skipped_for_cap: list[str]
    requests_this_month: int
    monthly_cap: int


class BenchmarkRead(BaseModel):
    since: date | None
    invested: Decimal
    portfolio_return_pct: Decimal | None
    cdi_return_pct: Decimal | None
    difference_pct: Decimal | None
    note: str
