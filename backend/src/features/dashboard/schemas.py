import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class DashboardSummary(BaseModel):
    income_total: Decimal
    expense_total: Decimal
    balance: Decimal


class CategorySpending(BaseModel):
    category_id: uuid.UUID
    category_name: str
    total: Decimal


class BalancePoint(BaseModel):
    date: date
    balance: Decimal


class DashboardRead(BaseModel):
    start_date: date
    end_date: date
    summary: DashboardSummary
    by_category: list[CategorySpending]
    balance_evolution: list[BalancePoint]
