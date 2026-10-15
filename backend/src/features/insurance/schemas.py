import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, model_validator

Kind = Literal["life", "health", "auto", "home", "travel", "other"]
Frequency = Literal["monthly", "annual"]
RenewalStatus = Literal["ok", "soon", "overdue", "inactive"]


class PolicyCreate(BaseModel):
    kind: Kind
    insurer: str = Field(min_length=1, max_length=120)
    name: str = Field(min_length=1, max_length=120)
    premium_amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    premium_frequency: Frequency
    coverage_amount: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    starts_on: date | None = None
    renews_on: date
    # Mensal: primeira cobrança (padrão: hoje).
    first_due_on: date | None = None
    asset_id: uuid.UUID | None = None
    payment_account_id: uuid.UUID
    category_id: uuid.UUID
    notes: str | None = Field(default=None, max_length=500)


class PolicyUpdate(BaseModel):
    kind: Kind | None = None
    insurer: str | None = Field(default=None, min_length=1, max_length=120)
    name: str | None = Field(default=None, min_length=1, max_length=120)
    premium_amount: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    coverage_amount: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    renews_on: date | None = None
    asset_id: uuid.UUID | None = None
    notes: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def _no_nulls_for_required(self) -> "PolicyUpdate":
        for field in ("kind", "insurer", "name", "premium_amount", "renews_on"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} nao pode ser removido")
        return self


class RenewRequest(BaseModel):
    premium_amount: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)


class PolicyRead(BaseModel):
    id: uuid.UUID
    kind: Kind
    insurer: str
    name: str
    premium_amount: Decimal
    premium_frequency: Frequency
    coverage_amount: Decimal | None
    starts_on: date | None
    renews_on: date
    first_due_on: date | None
    asset_id: uuid.UUID | None
    payment_account_id: uuid.UUID
    category_id: uuid.UUID
    recurring_id: uuid.UUID | None
    commitment_id: uuid.UUID | None
    is_active: bool
    notes: str | None
    created_at: datetime
    days_to_renewal: int
    renewal_status: RenewalStatus


class UninsuredAssetRead(BaseModel):
    asset_id: uuid.UUID
    name: str
    kind: str
    value: Decimal


class InsuranceSummary(BaseModel):
    active_count: int
    renewals_soon: list[PolicyRead]
    overdue_renewals: list[PolicyRead]
    uninsured_assets: list[UninsuredAssetRead]
    monthly_cost: Decimal
