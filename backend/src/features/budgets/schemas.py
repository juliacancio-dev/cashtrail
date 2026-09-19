import uuid
from decimal import Decimal

from pydantic import BaseModel, Field


class BudgetCreate(BaseModel):
    category_id: uuid.UUID
    month: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$", description="Ano-mês no formato YYYY-MM")
    limit_amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)


class BudgetUpdate(BaseModel):
    limit_amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)


class BudgetRead(BaseModel):
    id: uuid.UUID
    category_id: uuid.UUID
    category_name: str
    month: str
    limit_amount: Decimal
    spent_amount: Decimal
    percent_consumed: Decimal
    is_exceeded: bool
