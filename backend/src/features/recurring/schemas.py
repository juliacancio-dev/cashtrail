import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from src.features.recurring.models import RecurringFrequency
from src.features.transactions.models import TransactionType


class RecurringCreate(BaseModel):
    account_id: uuid.UUID
    category_id: uuid.UUID
    type: TransactionType
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    description: str | None = Field(default=None, max_length=255)
    frequency: RecurringFrequency
    next_occurrence_date: date
    # Padrão False preserva o comportamento do Marco 5 (gera o lançamento já realizado).
    generate_as_commitment: bool = False


class RecurringUpdate(BaseModel):
    amount: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    description: str | None = Field(default=None, max_length=255)
    frequency: RecurringFrequency | None = None


class RecurringRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_id: uuid.UUID
    category_id: uuid.UUID
    type: TransactionType
    amount: Decimal
    description: str | None
    frequency: RecurringFrequency
    next_occurrence_date: date
    is_active: bool
    generate_as_commitment: bool
    created_at: datetime
