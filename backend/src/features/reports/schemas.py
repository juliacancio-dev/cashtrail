import uuid
from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel

AccountKind = Literal["checking", "savings", "credit_card", "loan"]


class AccountBalanceRead(BaseModel):
    account_id: uuid.UUID
    name: str
    type: AccountKind
    is_archived: bool
    opening_balance: Decimal
    balance: Decimal


class BalancesRead(BaseModel):
    accounts: list[AccountBalanceRead]
    cash_total: Decimal
    card_debt_total: Decimal
    loan_debt_total: Decimal


class DreCategoryRead(BaseModel):
    category_id: uuid.UUID | None
    name: str
    amount: Decimal


class DreLineRead(BaseModel):
    key: str
    label: str
    kind: Literal["group", "subtotal", "ungrouped"]
    amount: Decimal
    previous_amount: Decimal
    percent_of_net_revenue: Decimal | None
    categories: list[DreCategoryRead]


class DreRead(BaseModel):
    start_date: date
    end_date: date
    previous_start_date: date
    previous_end_date: date
    include_forecast: bool
    lines: list[DreLineRead]
    net_result: Decimal
    previous_net_result: Decimal
    ungrouped_count: int


class SourceTotalsRead(BaseModel):
    planned_in: Decimal
    planned_out: Decimal
    realized_in: Decimal
    realized_out: Decimal


class CashFlowMonthRead(BaseModel):
    month: str
    status: Literal["past", "current", "future"]
    opening_balance: Decimal
    planned_in: Decimal
    planned_out: Decimal
    realized_in: Decimal
    realized_out: Decimal
    projected_in: Decimal
    projected_out: Decimal
    closing_projected: Decimal
    closing_realized: Decimal | None
    variance_in: Decimal
    variance_out: Decimal
    sources: dict[str, SourceTotalsRead]


class CashFlowRead(BaseModel):
    start_month: str
    months: list[CashFlowMonthRead]
    cash_balance_today: Decimal
    warnings: list[str]


class FlowItemRead(BaseModel):
    column: Literal["realized", "planned"]
    direction: Literal["in", "out"]
    when: date
    amount: Decimal
    source: str
    description: str
    category_id: uuid.UUID | None
    category_name: str | None


class NetWorthAccountRead(BaseModel):
    account_id: uuid.UUID
    name: str
    amount: Decimal
    is_archived: bool


class NetWorthAssetRead(BaseModel):
    asset_id: uuid.UUID
    name: str
    kind: str
    value: Decimal
    valued_at: date | None
    is_stale: bool
    debt_outstanding: Decimal | None
    equity: Decimal


class NetWorthDebtRead(BaseModel):
    account_id: uuid.UUID
    name: str
    amount: Decimal
    short_term: Decimal | None
    long_term: Decimal | None


class NetWorthRead(BaseModel):
    as_of: date
    cash: list[NetWorthAccountRead]
    assets: list[NetWorthAssetRead]
    cards: list[NetWorthAccountRead]
    debts: list[NetWorthDebtRead]
    cash_total: Decimal
    assets_total: Decimal
    total_assets: Decimal
    cards_total: Decimal
    debts_total: Decimal
    debts_short_term: Decimal | None
    debts_long_term: Decimal | None
    total_liabilities: Decimal
    net_worth: Decimal
    warnings: list[str]


class NetWorthPointRead(BaseModel):
    month: str
    as_of: date
    total_assets: Decimal
    total_liabilities: Decimal
    net_worth: Decimal
