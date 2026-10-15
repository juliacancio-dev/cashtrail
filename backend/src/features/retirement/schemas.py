from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PlanWrite(BaseModel):
    current_age: int = Field(ge=0, le=120)
    target_age: int = Field(ge=1, le=120)
    monthly_income_wanted: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    public_benefit_monthly: Decimal = Field(default=Decimal("0"), ge=0, max_digits=12, decimal_places=2)
    # Frações: 0.04 = 4%.
    real_return_annual: Decimal = Field(default=Decimal("0.04"), ge=Decimal("-0.2"), le=Decimal("0.3"), max_digits=6, decimal_places=4)
    withdrawal_rate: Decimal = Field(default=Decimal("0.04"), gt=0, le=Decimal("0.2"), max_digits=6, decimal_places=4)
    monthly_contribution: Decimal = Field(default=Decimal("0"), ge=0, max_digits=12, decimal_places=2)
    include_assets: bool = False


class PlanRead(PlanWrite):
    model_config = ConfigDict(from_attributes=True)

    updated_at: datetime


class ScenarioRead(BaseModel):
    withdrawal_rate: Decimal
    real_return: Decimal
    target: Decimal
    months: int | None
    age: Decimal | None
    is_base: bool


class ResultRead(BaseModel):
    target: Decimal
    progress_pct: Decimal
    sustainable_income_today: Decimal
    months_to_target: int | None
    age_at_target: Decimal | None
    reaches_by_target_age: bool
    required_contribution: Decimal
    gap: Decimal
    scenarios: list[ScenarioRead]


class OverviewRead(BaseModel):
    disclaimer: str
    plan: PlanRead | None
    invested_wealth: Decimal
    assets_wealth: Decimal
    counted_wealth: Decimal
    result: ResultRead | None
    ipca_12m_pct: Decimal | None
    defaults: dict[str, Decimal]
    warnings: list[str]
