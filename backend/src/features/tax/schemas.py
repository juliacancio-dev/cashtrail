import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

StatementKind = Literal["salary", "other_taxable", "thirteenth", "plr", "exclusive_other", "exempt"]
Amount = Field(default=Decimal("0"), ge=0, max_digits=14, decimal_places=2)


class StatementCreate(BaseModel):
    payer_name: str = Field(min_length=1, max_length=120)
    kind: StatementKind
    gross_income: Decimal = Amount
    social_security: Decimal = Amount
    withheld_tax: Decimal = Amount
    note: str | None = Field(default=None, max_length=255)


class StatementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    year: int
    payer_name: str
    kind: StatementKind
    gross_income: Decimal
    social_security: Decimal
    withheld_tax: Decimal
    note: str | None
    created_at: datetime


class DependentsUpdate(BaseModel):
    count: int = Field(ge=0, le=20)


class KindTotals(BaseModel):
    gross: Decimal
    social_security: Decimal
    withheld: Decimal


class SourceRead(BaseModel):
    topic: str
    url: str
    kind: str


class ParametersRead(BaseModel):
    year: int
    label: str
    consulted_at: date
    sources: list[SourceRead]
    unverified: list[str]
    dependent_deduction: Decimal
    education_limit_per_person: Decimal
    simplified_limit: Decimal
    stock_exempt_monthly_sales: Decimal
    darf_code: str


class ModalityRead(BaseModel):
    name: str
    deductions: Decimal
    base: Decimal
    tax_before_reducer: Decimal
    reducer: Decimal
    tax_due: Decimal
    balance: Decimal


class EstimateRead(BaseModel):
    taxable_income: Decimal
    social_security: Decimal
    withheld_tax: Decimal
    health: Decimal
    education_declared: Decimal
    education_deducted: Decimal
    pension_declared: Decimal
    pension_deducted: Decimal
    dependents: int
    dependents_deduction: Decimal
    complete: ModalityRead
    simplified: ModalityRead
    best: str
    notes: list[str]


class MonthRead(BaseModel):
    month: str
    modality: str
    sales: Decimal
    gain: Decimal
    exempt: bool
    loss_used: Decimal
    loss_carried: Decimal
    taxable_gain: Decimal
    tax: Decimal
    irrf: Decimal
    darf_amount: Decimal
    darf_carried: Decimal
    due_date: date


class RightRead(BaseModel):
    group: str
    name: str
    amount: Decimal
    note: str | None


class DossierRead(BaseModel):
    year: int
    as_of: date
    disclaimer: str
    parameters: ParametersRead
    dependents: int
    statements: list[StatementRead]
    totals_by_kind: dict[str, KindTotals]
    estimate: EstimateRead
    variable_income: list[MonthRead]
    day_trade_flags: list[str]
    assets_and_rights: list[RightRead]
    debts: list[RightRead]
    untagged_expense_categories: int
    warnings: list[str]


class YearsRead(BaseModel):
    years: list[int]
    default_year: int
