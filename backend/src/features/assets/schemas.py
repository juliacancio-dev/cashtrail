import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Kind = Literal["real_estate", "vehicle", "other"]
Value = Field(ge=0, max_digits=14, decimal_places=2)


class AssetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    kind: Kind = "other"
    acquired_at: date | None = None
    acquisition_value: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    current_value: Decimal = Value
    valued_at: date | None = None
    debt_id: uuid.UUID | None = None


class AssetUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    kind: Kind | None = None
    acquired_at: date | None = None
    acquisition_value: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    debt_id: uuid.UUID | None = None
    disposed_at: date | None = None

    @model_validator(mode="after")
    def _no_nulls_for_required(self) -> "AssetUpdate":
        for field in ("name", "kind"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} nao pode ser removido")
        return self


class ValuationCreate(BaseModel):
    valued_at: date | None = None
    value: Decimal = Value
    note: str | None = Field(default=None, max_length=255)


class ValuationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    valued_at: date
    value: Decimal
    note: str | None
    created_at: datetime


class AssetRead(BaseModel):
    id: uuid.UUID
    name: str
    kind: Kind
    acquired_at: date | None
    acquisition_value: Decimal | None
    debt_id: uuid.UUID | None
    disposed_at: date | None
    value: Decimal
    valued_at: date | None
    is_stale: bool


class AssetDetail(AssetRead):
    valuations: list[ValuationRead]
