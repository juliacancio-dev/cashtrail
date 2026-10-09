import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.features.commitments.models import CommitmentDirection

CommitmentStatus = Literal["open", "due_today", "overdue", "partially_paid", "paid", "canceled"]
StatusFilter = Literal["pending", "open", "due_today", "overdue", "partially_paid", "paid", "canceled"]

Money = Field(gt=0, max_digits=12, decimal_places=2)


class CommitmentCreate(BaseModel):
    direction: CommitmentDirection
    description: str = Field(min_length=1, max_length=255)
    counterparty: str | None = Field(default=None, max_length=255)
    # TOTAL: com installments > 1 é dividido entre as parcelas (RB-012).
    amount: Decimal = Money
    due_date: date
    category_id: uuid.UUID
    account_id: uuid.UUID | None = None
    notes: str | None = Field(default=None, max_length=1000)
    installments: int = Field(default=1, ge=1, le=120)


class CommitmentUpdate(BaseModel):
    description: str | None = Field(default=None, min_length=1, max_length=255)
    counterparty: str | None = Field(default=None, max_length=255)
    amount: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    due_date: date | None = None
    category_id: uuid.UUID | None = None
    account_id: uuid.UUID | None = None
    notes: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def required_fields_cannot_be_cleared(self) -> "CommitmentUpdate":
        for field in ("description", "amount", "due_date", "category_id"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} nao pode ser removido")
        return self


class SettlementCreate(BaseModel):
    # Sem `amount`, baixa o saldo inteiro. Com valor menor, é baixa parcial (RF-017).
    amount: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    paid_at: date | None = None
    account_id: uuid.UUID | None = None


class SettlementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    commitment_id: uuid.UUID
    transaction_id: uuid.UUID
    amount: Decimal
    paid_at: date
    created_at: datetime


class CommitmentRead(BaseModel):
    id: uuid.UUID
    direction: CommitmentDirection
    description: str
    counterparty: str | None
    amount: Decimal
    due_date: date
    category_id: uuid.UUID
    account_id: uuid.UUID | None
    notes: str | None
    recurring_transaction_id: uuid.UUID | None
    installment_group_id: uuid.UUID | None
    installment_number: int | None
    installment_count: int | None
    is_canceled: bool
    created_at: datetime
    paid_amount: Decimal
    balance: Decimal
    status: CommitmentStatus


class CommitmentDetail(CommitmentRead):
    settlements: list[SettlementRead]


class CommitmentTotals(BaseModel):
    count: int
    payable_balance: Decimal
    receivable_balance: Decimal


class CommitmentList(BaseModel):
    items: list[CommitmentRead]
    totals: CommitmentTotals


class DirectionSummary(BaseModel):
    overdue_count: int
    overdue_amount: Decimal
    due_soon_count: int
    due_soon_amount: Decimal
    open_amount: Decimal


class CommitmentSummary(BaseModel):
    days: int
    payable: DirectionSummary
    receivable: DirectionSummary
