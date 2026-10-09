import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from src.features.accounts.models import AccountType


class AccountCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    type: AccountType
    # Pode ser negativo (conta no vermelho, ou dívida inicial de um cartão).
    opening_balance: Decimal = Field(default=Decimal("0"), max_digits=12, decimal_places=2)


class AccountUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    opening_balance: Decimal | None = Field(default=None, max_digits=12, decimal_places=2)


class AccountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    type: AccountType
    opening_balance: Decimal
    is_archived: bool
    created_at: datetime
