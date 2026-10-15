import uuid
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.features.assets import service as assets_service
from src.features.investments import service as investments_service
from src.features.investments.providers import BcbProvider, IndexError_, IndexProvider
from src.features.retirement import calc
from src.features.retirement.models import RetirementPlan

DEFAULTS = {
    "withdrawal_rate": Decimal("0.04"),
    "real_return_annual": Decimal("0.04"),
}


class InvalidPlanError(Exception):
    """Idade-alvo menor ou igual à atual, ou premissas fora dos limites."""


@dataclass(frozen=True)
class Overview:
    plan: RetirementPlan | None
    invested_wealth: Decimal
    assets_wealth: Decimal
    counted_wealth: Decimal
    result: calc.Result | None
    ipca_12m_pct: Decimal | None
    warnings: list[str]


def get_plan(db: Session, user_id: uuid.UUID) -> RetirementPlan | None:
    return db.scalar(select(RetirementPlan).where(RetirementPlan.user_id == user_id))


def save_plan(
    db: Session,
    user_id: uuid.UUID,
    current_age: int,
    target_age: int,
    monthly_income_wanted: Decimal,
    public_benefit_monthly: Decimal,
    real_return_annual: Decimal,
    withdrawal_rate: Decimal,
    monthly_contribution: Decimal,
    include_assets: bool,
) -> RetirementPlan:
    if target_age <= current_age:
        raise InvalidPlanError("target_age")
    plan = get_plan(db, user_id)
    if plan is None:
        plan = RetirementPlan(user_id=user_id)
        db.add(plan)
    plan.current_age = current_age
    plan.target_age = target_age
    plan.monthly_income_wanted = monthly_income_wanted
    plan.public_benefit_monthly = public_benefit_monthly
    plan.real_return_annual = real_return_annual
    plan.withdrawal_rate = withdrawal_rate
    plan.monthly_contribution = monthly_contribution
    plan.include_assets = include_assets
    db.commit()
    db.refresh(plan)
    return plan


# O IPCA muda uma vez por mês: guardar o acumulado do dia evita bater no Banco Central a cada abertura da tela.
# Só cacheia o provedor real (os testes usam provedores falsos e não podem se contaminar).
_IPCA_CACHE: dict[date, Decimal] = {}


def _ipca_12m(provider: IndexProvider, today: date) -> Decimal | None:
    cacheable = isinstance(provider, BcbProvider)
    if cacheable and today in _IPCA_CACHE:
        return _IPCA_CACHE[today]
    value = _fetch_ipca_12m(provider, today)
    if cacheable and value is not None:
        _IPCA_CACHE[today] = value
    return value


def _fetch_ipca_12m(provider: IndexProvider, today: date) -> Decimal | None:
    try:
        rows = provider.ipca_monthly(today - timedelta(days=430), today)
    except (IndexError_, AttributeError):
        return None
    last = [value for _, value in sorted(rows)[-12:]]
    if len(last) < 12:
        return None
    factor = Decimal(1)
    for value in last:
        factor *= Decimal(1) + value / Decimal(100)
    return ((factor - 1) * 100).quantize(Decimal("0.01"))


def overview(
    db: Session, user_id: uuid.UUID, index_provider: IndexProvider, today: date | None = None
) -> Overview:
    """RF-073/RF-074: patrimônio investido de hoje contra o alvo, com cenários."""
    today = today or date.today()
    plan = get_plan(db, user_id)

    invested = sum(
        (v.market_value for v in investments_service.portfolio(db, user_id, today, include_empty=False)),
        Decimal("0.00"),
    )
    owned = sum(
        (a.value for a in assets_service.list_views(db, user_id, today) if a.asset.disposed_at is None),
        Decimal("0.00"),
    )
    counted = invested + (owned if plan is not None and plan.include_assets else Decimal("0.00"))

    warnings: list[str] = []
    result = None
    if plan is not None:
        result = calc.evaluate(
            plan.current_age,
            plan.target_age,
            plan.monthly_income_wanted,
            plan.public_benefit_monthly,
            plan.real_return_annual,
            plan.withdrawal_rate,
            plan.monthly_contribution,
            counted,
        )
        if plan.withdrawal_rate > Decimal("0.05"):
            warnings.append("Taxa de retirada acima de 5%: é uma premissa agressiva para um horizonte longo.")
        if plan.real_return_annual > Decimal("0.07"):
            warnings.append("Retorno real acima de 7% ao ano é uma premissa otimista; veja os cenários.")
        if result.months_to_target is None:
            warnings.append("Com estas premissas o alvo não é atingido em 80 anos.")
    return Overview(
        plan=plan,
        invested_wealth=invested.quantize(Decimal("0.01")),
        assets_wealth=owned.quantize(Decimal("0.01")),
        counted_wealth=counted.quantize(Decimal("0.01")),
        result=result,
        ipca_12m_pct=_ipca_12m(index_provider, today),
        warnings=warnings,
    )
