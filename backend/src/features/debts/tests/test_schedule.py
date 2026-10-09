"""Calculadora de cronograma (RF-033/RF-040): exemplos de manual e propriedades."""

from decimal import Decimal

import pytest

from src.features.debts import schedule

D = Decimal


def test_price_matches_the_textbook_payment():
    rows = schedule.build(D("10000"), "price", D("0.02"), 12)

    assert rows[0].payment == D("945.60")
    assert rows[0].interest == D("200.00")
    assert rows[0].principal == D("745.60")
    assert len(rows) == 12
    assert rows[-1].balance == D("0.00")


def test_sac_has_constant_amortization_and_falling_payments():
    rows = schedule.build(D("1200"), "sac", D("0.01"), 12)

    assert [r.principal for r in rows[:-1]] == [D("100.00")] * 11
    assert rows[0].payment == D("112.00")
    assert rows[1].payment == D("111.00")
    assert rows[-1].balance == D("0.00")


def test_zero_rate_splits_evenly_and_last_installment_absorbs_rounding():
    rows = schedule.build(D("100"), "zero", D("0.05"), 3)  # a taxa é ignorada em "zero"

    assert [r.principal for r in rows] == [D("33.33"), D("33.33"), D("33.34")]
    assert all(r.interest == D("0.00") for r in rows)


@pytest.mark.parametrize("system", ["price", "sac", "zero"])
@pytest.mark.parametrize("principal", [D("1000"), D("12345.67"), D("999.99"), D("50000")])
@pytest.mark.parametrize("count", [1, 2, 7, 24, 48, 360])
@pytest.mark.parametrize("rate", [D("0"), D("0.0099"), D("0.0299")])
def test_principal_always_sums_to_the_amount_and_balance_ends_at_zero(system, principal, count, rate):
    rows = schedule.build(principal, system, rate, count)

    assert sum((r.principal for r in rows), D("0")) == principal
    assert rows[-1].balance == D("0.00")
    assert all(r.principal >= 0 and r.interest >= 0 for r in rows)
    assert all(r.payment == r.principal + r.interest for r in rows)


def test_fixed_payment_cuts_the_term_and_keeps_the_payment():
    original = schedule.build(D("10000"), "price", D("0.02"), 12)
    paid = sum(r.principal for r in original[:3])
    balance_after_three = D("10000") - paid
    extra = D("2000")

    rows = schedule.fixed_payment(balance_after_three - extra, D("0.02"), original[0].payment)

    assert len(rows) < 9  # sobravam 9 parcelas
    assert rows[0].payment == D("945.60")
    assert rows[-1].payment <= D("945.60")
    assert sum((r.principal for r in rows), D("0")) == balance_after_three - extra


def test_fixed_payment_that_does_not_cover_interest_is_rejected():
    with pytest.raises(schedule.ScheduleError):
        schedule.fixed_payment(D("10000"), D("0.05"), D("400"))  # juros do mês = 500


def test_constant_amortization_cuts_the_term():
    rows = schedule.constant_amortization(D("500"), D("0.01"), D("100"))

    assert [r.principal for r in rows] == [D("100.00")] * 5
    assert rows[-1].balance == D("0.00")


def test_invalid_inputs_are_rejected():
    with pytest.raises(schedule.ScheduleError):
        schedule.build(D("0"), "price", D("0.01"), 12)
    with pytest.raises(schedule.ScheduleError):
        schedule.build(D("100"), "price", D("0.01"), 0)
    with pytest.raises(schedule.ScheduleError):
        schedule.build(D("100"), "bogus", D("0.01"), 12)
