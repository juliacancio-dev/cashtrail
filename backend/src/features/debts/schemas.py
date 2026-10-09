import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Money = Field(gt=0, max_digits=12, decimal_places=2)
System = Literal["price", "sac", "zero"]
AmortizationMode = Literal["reduce_term", "reduce_installment", "payoff"]
InstallmentStatus = Literal["open", "due_today", "overdue", "paid", "canceled", "superseded", "partially_paid"]


class ScheduleParams(BaseModel):
    principal: Decimal = Money
    installments: int = Field(ge=1, le=360)
    first_due_date: date
    system: System = "price"
    # Percentual ao mês: 1.99 = 1,99% a.m.
    monthly_rate: Decimal = Field(default=Decimal("0"), ge=0, le=100, max_digits=7, decimal_places=4)


class DebtCreate(ScheduleParams):
    name: str = Field(min_length=1, max_length=120)
    creditor: str | None = Field(default=None, max_length=255)
    contracted_at: date
    interest_category_id: uuid.UUID
    payment_account_id: uuid.UUID | None = None
    # Conta que recebeu o dinheiro. Sem ela, a dívida é tratada como já existente (saldo inicial).
    received_account_id: uuid.UUID | None = None


class PlannedInstallmentRead(BaseModel):
    number: int
    due_date: date
    principal: Decimal
    charges: Decimal
    amount: Decimal
    balance: Decimal


class SchedulePreview(BaseModel):
    rows: list[PlannedInstallmentRead]
    total_paid: Decimal
    total_charges: Decimal


class InstallmentRead(BaseModel):
    id: uuid.UUID
    number: int
    commitment_id: uuid.UUID
    due_date: date
    amount: Decimal
    principal_part: Decimal
    charges: Decimal
    status: InstallmentStatus
    # Preenchido quando paga: usado para desfazer o pagamento.
    paid: bool


class InstallmentUpdate(BaseModel):
    amount: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    due_date: date | None = None


class InstallmentPay(BaseModel):
    paid_at: date | None = None
    account_id: uuid.UUID | None = None


class AmortizationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    amount: Decimal
    paid_at: date
    mode: str
    created_at: datetime


class NextInstallment(BaseModel):
    id: uuid.UUID
    number: int
    due_date: date
    amount: Decimal
    status: InstallmentStatus


class DebtRead(BaseModel):
    id: uuid.UUID
    account_id: uuid.UUID
    name: str
    creditor: str | None
    principal: Decimal
    contracted_at: date
    installments: int
    system: System
    monthly_rate: Decimal
    first_due_date: date
    payment_account_id: uuid.UUID | None
    interest_category_id: uuid.UUID
    outstanding: Decimal
    principal_paid: Decimal
    charges_paid: Decimal
    charges_projected: Decimal
    installments_paid: int
    installments_open: int
    next_installment: NextInstallment | None
    is_paid_off: bool


class DebtDetail(DebtRead):
    installment_list: list[InstallmentRead]
    amortizations: list[AmortizationRead]
    # id da parcela -> id da baixa (só parcelas pagas); a baixa é desfeita pela parcela.
    settlement_ids: dict[uuid.UUID, uuid.UUID]


class AmortizationCreate(BaseModel):
    # Ignorado em `payoff` (paga o saldo devedor inteiro).
    amount: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    mode: AmortizationMode = "reduce_term"
    paid_at: date | None = None
    account_id: uuid.UUID | None = None


class AmortizationPreviewRequest(BaseModel):
    amount: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    mode: AmortizationMode = "reduce_term"


class AmortizationPreview(BaseModel):
    outstanding_before: Decimal
    outstanding_after: Decimal
    installments_before: int
    installments_after: int
    charges_before: Decimal
    charges_after: Decimal
    rows: list[PlannedInstallmentRead]


class DebtsSummary(BaseModel):
    outstanding_total: Decimal
    active_count: int
    overdue_count: int
    next_due_date: date | None
    next_amount: Decimal | None
    next_debt_name: str | None
