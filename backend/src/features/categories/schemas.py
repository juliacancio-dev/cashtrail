import uuid
from datetime import datetime

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

DreGroup = Literal[
    "revenue", "deduction", "variable_expense", "fixed_expense", "financial_expense", "financial_revenue"
]


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    dre_group: DreGroup | None = None


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    # Enviar `null` explicitamente remove o grupo (volta para "Sem grupo").
    dre_group: DreGroup | None = None


class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    dre_group: DreGroup | None
    is_archived: bool
    created_at: datetime
