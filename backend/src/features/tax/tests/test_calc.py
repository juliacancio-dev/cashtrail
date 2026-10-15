"""Cálculo do IRPF contra a tabela oficial do ano-calendário 2026 (valores conferidos à mão)."""

from datetime import date
from decimal import Decimal

import pytest

from src.features.tax import calc, parameters

D = Decimal
P = parameters.load(2026)


def test_parameters_for_an_unknown_year_are_an_explicit_error():
    with pytest.raises(parameters.UnsupportedYearError):
        parameters.load(2019)


def test_parameters_carry_sources_and_the_unverified_list():
    assert P.consulted_at == date(2026, 10, 15)
    assert any("gov.br/receitafederal" in s["url"] for s in P.sources)
    assert P.unverified  # nada some em silêncio: o que não foi verificado fica registrado


@pytest.mark.parametrize(
    ("base", "expected"),
    [
        ("0", "0.00"),
        ("29145.60", "0.00"),  # teto da faixa isenta
        ("30000", "64.08"),  # 30000 × 7,5% − 2.185,92
        ("40000", "1270.09"),  # 40000 × 15% − 4.729,91
        ("50000", "3144.15"),  # 50000 × 22,5% − 8.105,85
        ("100000", "16595.34"),  # 100000 × 27,5% − 10.904,66
    ],
)
def test_progressive_table_matches_hand_calculation(base, expected):
    assert calc.progressive_tax(D(base), P) == D(expected)


@pytest.mark.parametrize(
    ("income", "expected"),
    [
        ("30000", "2694.15"),
        ("60000", "2694.15"),
        ("70000", "1739.48"),  # 8.429,73 − 0,095575 × 70.000
        ("88200", "0.00"),
        ("120000", "0.00"),
    ],
)
def test_reducer_of_law_15270(income, expected):
    assert calc.reducer_amount(D(income), P) == D(expected)


def estimate(**kw):
    base = dict(
        taxable_income=D("0"), social_security=D("0"), withheld_tax=D("0"), health=D("0"),
        education=D("0"), pension=D("0"), dependents=0, params=P,
    )
    base.update({k: D(v) if k != "dependents" and k != "params" else v for k, v in kw.items()})
    return calc.annual_estimate(**base)


def test_income_up_to_the_reducer_ceiling_pays_no_tax():
    e = estimate(taxable_income="60000", social_security="5000")

    # completa: base 55.000 → 4.269,15 − redutor 2.694,15 = 1.575,00; simplificada: base 48.000 → 2.694,15 − 2.694,15 = 0
    assert e.complete.tax_due == D("1575.00")
    assert e.simplified.tax_due == D("0.00")
    assert e.best == "simplificada"


def test_high_income_gets_no_reducer_and_picks_the_cheaper_modality():
    e = estimate(taxable_income="100000", social_security="8000", health="4000", education="5000",
                 withheld_tax="12000")

    assert e.education_deducted == D("3561.50")  # limite por pessoa
    assert e.complete.deductions == D("15561.50")
    assert e.complete.tax_due == D("12315.93")
    assert e.simplified.deductions == D("17640.00")  # 20% = 20.000, limitado a 17.640
    assert e.simplified.tax_due == D("11744.34")
    assert e.best == "simplificada"
    assert e.simplified.balance == D("-255.66")  # a restituir
    assert e.complete.balance == D("315.93")
    assert any("Educação acima do limite" in note for note in e.notes)


def test_dependents_raise_the_education_limit_and_add_their_deduction():
    e = estimate(taxable_income="100000", education="7000", dependents=1)

    assert e.dependents_deduction == D("2275.08")
    assert e.education_deducted == D("7000.00")  # limite = 2 pessoas × 3.561,50


def test_pension_is_limited_to_twelve_percent_of_taxable_income():
    e = estimate(taxable_income="100000", pension="20000")

    assert e.pension_deducted == D("12000.00")


@pytest.mark.parametrize("income", ["0", "1000", "29145.60", "60000", "88200", "250000"])
def test_tax_is_never_negative_and_balance_is_due_minus_withheld(income):
    e = estimate(taxable_income=income, withheld_tax="500")

    for modality in (e.complete, e.simplified):
        assert modality.tax_due >= 0
        assert modality.balance == modality.tax_due - D("500.00")
        assert modality.reducer <= modality.tax_before_reducer


# ---------- renda variável ----------

def sale(day, modality, gross, gain):
    return calc.Sale(day, modality, D(gross), D(gain))


def test_stock_sales_up_to_the_monthly_limit_are_exempt():
    [month] = calc.variable_income([sale(date(2026, 3, 10), "stock", "15000", "2000")], P)

    assert month.exempt is True
    assert (month.tax, month.darf_amount) == (D("0.00"), D("0.00"))


def test_stock_sales_above_the_limit_pay_15_percent_of_the_whole_gain():
    [month] = calc.variable_income([sale(date(2026, 3, 10), "stock", "25000", "2000")], P)

    assert month.exempt is False
    assert month.tax == D("300.00")
    assert month.irrf == D("1.25")  # 0,005% × 25.000
    assert month.darf_amount == D("298.75")
    assert month.due_date == date(2026, 4, 30)


def test_losses_carry_forward_and_offset_later_gains_of_the_same_modality():
    months = calc.variable_income(
        [sale(date(2026, 3, 10), "stock", "30000", "-1000"), sale(date(2026, 4, 10), "stock", "30000", "3000")], P
    )

    march, april = months
    assert (march.tax, march.loss_carried) == (D("0.00"), D("1000.00"))
    assert (april.loss_used, april.taxable_gain, april.tax) == (D("1000.00"), D("2000.00"), D("300.00"))
    assert april.loss_carried == D("0.00")


def test_loss_in_a_stock_does_not_offset_fii_gains():
    months = calc.variable_income(
        [sale(date(2026, 3, 10), "stock", "30000", "-1000"), sale(date(2026, 3, 12), "fii", "5000", "500")], P
    )

    fii = next(m for m in months if m.modality == "fii")
    assert (fii.loss_used, fii.tax) == (D("0.00"), D("100.00"))  # 20%, sem isenção


def test_darf_below_the_minimum_accumulates_to_the_next_month():
    months = calc.variable_income(
        [sale(date(2026, 3, 10), "stock", "25000", "70"), sale(date(2026, 4, 10), "stock", "25000", "100")], P
    )

    march, april = months
    assert march.tax == D("10.50") and march.irrf == D("1.25")
    assert march.darf_amount == D("0.00") and march.darf_carried == D("9.25")
    assert april.darf_amount == D("9.25") + D("15.00") - D("1.25")


@pytest.mark.parametrize(
    ("day", "expected"),
    [
        (date(2026, 2, 1), date(2026, 3, 31)),  # terça
        (date(2026, 10, 5), date(2026, 11, 30)),  # segunda
        (date(2026, 1, 10), date(2026, 2, 27)),  # 28/02 é sábado → sexta
        (date(2026, 12, 20), date(2027, 1, 29)),  # 31/01/2027 é domingo → sexta 29
    ],
)
def test_darf_due_date_is_the_last_business_day_of_the_next_month(day, expected):
    assert calc.last_business_day_of_next_month(day) == expected
