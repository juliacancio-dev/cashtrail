import uuid
from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel

AccountKind = Literal["checking", "savings", "credit_card"]


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
