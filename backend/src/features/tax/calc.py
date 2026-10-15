"""Cálculo do IRPF (Marco 14): estimativa anual e apuração mensal de renda variável.

Funções puras, sem banco. Toda regra e todo valor vêm de `TaxParameters` (RB-042). É uma ESTIMATIVA:
o programa da Receita prevalece, e as premissas não verificadas estão em `parameters.unverified`.
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

from src.features.tax.parameters import TaxParameters

ZERO = Decimal("0.00")
CENT = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


# ---------- imposto anual ----------

def progressive_tax(base: Decimal, params: TaxParameters) -> Decimal:
    """Tabela progressiva: base × alíquota − parcela a deduzir, na faixa da base; nunca negativo."""
    if base <= 0:
        return ZERO
    for band in params.annual_table:
        if band.up_to is None or base <= band.up_to:
            return max(money(base * band.rate - band.deduction), ZERO)
    return ZERO


def reducer_amount(gross_taxable_income: Decimal, params: TaxParameters) -> Decimal:
    """Redutor da Lei 15.270/2025 sobre o imposto. Premissa: base = rendimentos tributáveis (ver `unverified`)."""
    r = params.reducer
    if gross_taxable_income <= r.full_up_to:
        return r.full_amount
    if gross_taxable_income >= r.phase_out_up_to:
        return ZERO  # a fórmula dá centavos no teto por arredondamento; a Receita diz que zera em R$ 88.200,00
    if gross_taxable_income < r.phase_out_up_to:
        return max(money(r.phase_constant - r.phase_factor * gross_taxable_income), ZERO)
    return ZERO


@dataclass(frozen=True)
class Modality:
    name: str  # "completa" | "simplificada"
    deductions: Decimal
    base: Decimal
    tax_before_reducer: Decimal
    reducer: Decimal
    tax_due: Decimal
    balance: Decimal  # > 0 a pagar; < 0 a restituir (já descontado o imposto retido)


@dataclass(frozen=True)
class AnnualEstimate:
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
    complete: Modality
    simplified: Modality
    best: str
    notes: list[str] = field(default_factory=list)


def _modality(name: str, deductions: Decimal, taxable: Decimal, withheld: Decimal, params: TaxParameters) -> Modality:
    base = max(taxable - deductions, ZERO)
    before = progressive_tax(base, params)
    reduction = min(reducer_amount(taxable, params), before)
    due = before - reduction
    return Modality(name, money(deductions), money(base), before, money(reduction), money(due), money(due - withheld))


def annual_estimate(
    taxable_income: Decimal,
    social_security: Decimal,
    withheld_tax: Decimal,
    health: Decimal,
    education: Decimal,
    pension: Decimal,
    dependents: int,
    params: TaxParameters,
) -> AnnualEstimate:
    """Completa × simplificada (RF-063). A simplificada substitui TODAS as deduções legais."""
    persons = 1 + dependents
    education_cap = params.education_limit_per_person * persons
    education_ded = min(education, education_cap)
    pension_ded = min(pension, money(taxable_income * params.pension_limit_rate))
    dependents_ded = params.dependent_deduction * dependents

    complete_deductions = social_security + health + education_ded + pension_ded + dependents_ded
    simplified_deduction = min(money(taxable_income * params.simplified_rate), params.simplified_limit)

    complete = _modality("completa", complete_deductions, taxable_income, withheld_tax, params)
    simplified = _modality("simplificada", simplified_deduction, taxable_income, withheld_tax, params)
    best = "completa" if complete.tax_due <= simplified.tax_due else "simplificada"

    notes: list[str] = []
    if education > education_cap:
        notes.append(f"Educação acima do limite: {money(education - education_cap)} não é dedutível.")
    if pension > pension_ded:
        notes.append("Previdência acima de 12% dos rendimentos tributáveis: o excedente não é dedutível.")

    return AnnualEstimate(
        taxable_income=money(taxable_income),
        social_security=money(social_security),
        withheld_tax=money(withheld_tax),
        health=money(health),
        education_declared=money(education),
        education_deducted=money(education_ded),
        pension_declared=money(pension),
        pension_deducted=money(pension_ded),
        dependents=dependents,
        dependents_deduction=money(dependents_ded),
        complete=complete,
        simplified=simplified,
        best=best,
        notes=notes,
    )


# ---------- renda variável (apuração mensal) ----------

@dataclass(frozen=True)
class Sale:
    occurred_at: date
    modality: str  # "stock" | "fii"
    gross: Decimal  # quantidade × preço, sem taxas (base da isenção e do IRRF)
    gain: Decimal  # ganho líquido da venda (já considera custo médio e taxas)


@dataclass(frozen=True)
class MonthResult:
    month: str  # AAAA-MM
    modality: str
    sales: Decimal
    gain: Decimal
    exempt: bool
    loss_used: Decimal
    loss_carried: Decimal  # prejuízo acumulado ao fim do mês
    taxable_gain: Decimal
    tax: Decimal
    irrf: Decimal
    darf_amount: Decimal  # a pagar (0 se abaixo do mínimo, que acumula)
    darf_carried: Decimal  # imposto abaixo do mínimo acumulado para o mês seguinte
    due_date: date


def last_business_day_of_next_month(day: date) -> date:
    """Prazo do DARF. Só fins de semana: feriados nacionais não são considerados (conferir no DARF)."""
    first_of_next = (day.replace(day=1) + timedelta(days=32)).replace(day=1)
    cursor = (first_of_next + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    while cursor.weekday() >= 5:
        cursor -= timedelta(days=1)
    return cursor


def variable_income(sales: list[Sale], params: TaxParameters) -> list[MonthResult]:
    """RF-064: apura mês a mês cada modalidade (RB-039, RB-040). Prejuízo só compensa a mesma modalidade."""
    vi = params.variable_income
    results: list[MonthResult] = []
    months = sorted({(s.occurred_at.year, s.occurred_at.month) for s in sales})

    for modality in ("stock", "fii"):
        loss = ZERO
        carried_darf = ZERO
        for year, month in months:
            chosen = [
                s for s in sales
                if s.modality == modality and (s.occurred_at.year, s.occurred_at.month) == (year, month)
            ]
            if not chosen:
                continue
            total_sales = money(sum((s.gross for s in chosen), ZERO))
            gain = money(sum((s.gain for s in chosen), ZERO))
            rate = vi.stock_rate if modality == "stock" else vi.fii_rate
            exempt = modality == "stock" and total_sales <= vi.stock_exempt_monthly_sales

            loss_used = ZERO
            taxable = ZERO
            if gain < 0:
                loss += -gain
            elif not exempt:
                loss_used = min(loss, gain)
                loss -= loss_used
                taxable = gain - loss_used

            tax = money(taxable * rate)
            irrf = money(total_sales * vi.irrf_rate)
            pending = max(tax - irrf, ZERO) + carried_darf
            if pending >= vi.darf_minimum:
                darf, carried_darf = money(pending), ZERO
            else:
                darf, carried_darf = ZERO, money(pending)

            results.append(
                MonthResult(
                    month=f"{year}-{month:02d}",
                    modality=modality,
                    sales=total_sales,
                    gain=gain,
                    exempt=exempt,
                    loss_used=money(loss_used),
                    loss_carried=money(loss),
                    taxable_gain=money(taxable),
                    tax=tax,
                    irrf=irrf,
                    darf_amount=darf,
                    darf_carried=carried_darf,
                    due_date=last_business_day_of_next_month(date(year, month, 1)),
                )
            )
    return sorted(results, key=lambda r: (r.month, r.modality))
