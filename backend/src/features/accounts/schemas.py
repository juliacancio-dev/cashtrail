import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from src.features.accounts.models import AccountType


class AccountCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    type: AccountType


class AccountUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)


class AccountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    type: AccountType
    is_archived: bool
    created_at: datetime
