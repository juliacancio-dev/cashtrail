"""Independência financeira em VALORES REAIS (RB-045 a RB-048). Funções puras, sem banco.

Não prevê nada: aplica premissas do usuário (retorno real, taxa de retirada, aporte) ao patrimônio atual.
"""

from dataclasses import dataclass
from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")
MAX_MONTHS = 12 * 80  # horizonte máximo de busca


def money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def money_up(value: Decimal) -> Decimal:
    """Arredonda PARA CIMA: o aporte calculado nunca pode ficar um centavo abaixo do necessário."""
    return value.quantize(CENT, rounding=ROUND_CEILING)


def monthly_rate(annual: Decimal) -> Decimal:
    """Taxa mensal equivalente (composta) à anual."""
    return (Decimal(1) + annual) ** (Decimal(1) / Decimal(12)) - Decimal(1)


def target_wealth(income_wanted: Decimal, public_benefit: Decimal, withdrawal_rate: Decimal) -> Decimal:
    """RB-046: o que falta da renda desejada depois do benefício público, anualizado, dividido pela taxa."""
    needed = max(income_wanted - public_benefit, Decimal(0))
    return money(needed * 12 / withdrawal_rate)


def months_to_target(current: Decimal, target: Decimal, annual_return: Decimal, monthly_contribution: Decimal) -> int | None:
    """Meses até o patrimônio atingir o alvo (0 se já atingiu; None se não atinge em 80 anos)."""
    if current >= target:
        return 0
    i = monthly_rate(annual_return)
    balance = current
    for month in range(1, MAX_MONTHS + 1):
        balance = balance * (Decimal(1) + i) + monthly_contribution
        if balance >= target:
            return month
    return None


def required_contribution(current: Decimal, target: Decimal, annual_return: Decimal, months: int) -> Decimal:
    """Aporte mensal para chegar ao alvo em `months` (0 se o patrimônio atual já basta)."""
    if months <= 0:
        return money_up(max(target - current, Decimal(0)))
    i = monthly_rate(annual_return)
    if i == 0:
        needed = (target - current) / months
    else:
        growth = (Decimal(1) + i) ** months
        needed = (target - current * growth) * i / (growth - Decimal(1))
    return money_up(max(needed, Decimal(0)))


@dataclass(frozen=True)
class Scenario:
    withdrawal_rate: Decimal
    real_return: Decimal
    target: Decimal
    months: int | None
    age: Decimal | None
    is_base: bool


@dataclass(frozen=True)
class Result:
    target: Decimal
    progress_pct: Decimal
    sustainable_income_today: Decimal  # o que o patrimônio atual já sustenta por mês (com benefício)
    months_to_target: int | None
    age_at_target: Decimal | None
    reaches_by_target_age: bool
    required_contribution: Decimal
    gap: Decimal
    scenarios: list[Scenario]


def evaluate(
    current_age: int,
    target_age: int,
    income_wanted: Decimal,
    public_benefit: Decimal,
    annual_return: Decimal,
    withdrawal_rate: Decimal,
    monthly_contribution: Decimal,
    current_wealth: Decimal,
) -> Result:
    target = target_wealth(income_wanted, public_benefit, withdrawal_rate)
    progress = (current_wealth / target * 100) if target > 0 else Decimal(100)
    sustainable = money(current_wealth * withdrawal_rate / 12 + public_benefit)

    months = months_to_target(current_wealth, target, annual_return, monthly_contribution)
    horizon = max((target_age - current_age) * 12, 0)
    age_at = None if months is None else (Decimal(current_age) + Decimal(months) / 12).quantize(Decimal("0.1"))

    # Grade de sensibilidade: três taxas de retirada × três retornos reais (RF-074).
    rates = sorted({Decimal("0.035"), withdrawal_rate, Decimal("0.05")})
    returns = [annual_return - Decimal("0.02"), annual_return, annual_return + Decimal("0.02")]
    scenarios: list[Scenario] = []
    for w in rates:
        t = target_wealth(income_wanted, public_benefit, w)
        for r in returns:
            m = months_to_target(current_wealth, t, r, monthly_contribution)
            scenarios.append(
                Scenario(
                    withdrawal_rate=w,
                    real_return=r,
                    target=t,
                    months=m,
                    age=None if m is None else (Decimal(current_age) + Decimal(m) / 12).quantize(Decimal("0.1")),
                    is_base=(w == withdrawal_rate and r == annual_return),
                )
            )

    return Result(
        target=target,
        progress_pct=progress.quantize(CENT, rounding=ROUND_HALF_UP),
        sustainable_income_today=sustainable,
        months_to_target=months,
        age_at_target=age_at,
        reaches_by_target_age=months is not None and months <= horizon,
        required_contribution=required_contribution(current_wealth, target, annual_return, horizon),
        gap=money(max(target - current_wealth, Decimal(0))),
        scenarios=scenarios,
    )
