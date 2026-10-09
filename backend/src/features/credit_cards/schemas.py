import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, model_validator

InvoiceStatus = Literal["future", "open", "closed", "overdue", "paid"]


class CardCreate(BaseModel):
    account_id: uuid.UUID
    closing_day: int = Field(ge=1, le=31)
    due_day: int = Field(ge=1, le=31)
    credit_limit: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    default_payment_account_id: uuid.UUID | None = None


class CardUpdate(BaseModel):
    closing_day: int | None = Field(default=None, ge=1, le=31)
    due_day: int | None = Field(default=None, ge=1, le=31)
    credit_limit: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    default_payment_account_id: uuid.UUID | None = None

    @model_validator(mode="after")
    def required_days_cannot_be_cleared(self) -> "CardUpdate":
        for field in ("closing_day", "due_day"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} nao pode ser removido")
        return self


class CardRead(BaseModel):
    id: uuid.UUID
    account_id: uuid.UUID
    account_name: str
    closing_day: int
    due_day: int
    credit_limit: Decimal | None
    default_payment_account_id: uuid.UUID | None
    debt: Decimal
    available: Decimal | None
    over_limit: bool
    created_at: datetime


class PurchaseCreate(BaseModel):
    description: str = Field(min_length=1, max_length=255)
    # TOTAL: com installments > 1 é dividido entre as parcelas.
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    purchase_date: date
    category_id: uuid.UUID
    installments: int = Field(default=1, ge=1, le=60)
    # Padrão: calculada pela data da compra. Informe um fechamento para escolher a fatura.
    invoice_closing_date: date | None = None


class PurchaseMove(BaseModel):
    invoice_closing_date: date


class PurchaseRead(BaseModel):
    transaction_id: uuid.UUID
    description: str | None
    amount: Decimal
    type: Literal["income", "expense"]
    occurred_at: date
    category_id: uuid.UUID
    invoice_closing_date: date
    moved: bool


class PaymentCreate(BaseModel):
    # Sem `amount`, paga o saldo inteiro da fatura. Com valor menor, o resto fica na fatura.
    amount: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    paid_at: date | None = None
    from_account_id: uuid.UUID | None = None


class PaymentRead(BaseModel):
    id: uuid.UUID
    transfer_id: uuid.UUID
    amount: Decimal
    paid_at: date
    created_at: datetime


class InvoiceRead(BaseModel):
    closing_date: date
    period_start: date
    due_date: date
    status: InvoiceStatus
    total: Decimal
    paid: Decimal
    balance: Decimal
    previous_closing_date: date
    next_closing_date: date
    purchases_count: int


class InvoiceDetail(InvoiceRead):
    purchases: list[PurchaseRead]
    payments: list[PaymentRead]


class CardsSummary(BaseModel):
    days: int
    overdue_count: int
    overdue_amount: Decimal
    due_soon_count: int
    due_soon_amount: Decimal
    debt: Decimal
