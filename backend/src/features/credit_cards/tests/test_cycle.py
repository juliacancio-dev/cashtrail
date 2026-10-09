"""RB-019/RB-021: matemática do ciclo da fatura (funções puras)."""

from datetime import date
from decimal import Decimal

import pytest

from src.features.credit_cards import cycle


@pytest.mark.parametrize(
    ("purchase", "closing_day", "expected"),
    [
        (date(2026, 10, 3), 5, date(2026, 10, 5)),    # antes do fechamento: fatura do mês
        (date(2026, 10, 5), 5, date(2026, 10, 5)),    # NO dia do fechamento: inclusive (RB-019)
        (date(2026, 10, 6), 5, date(2026, 11, 5)),    # um dia depois: fatura seguinte
        (date(2026, 12, 20), 5, date(2027, 1, 5)),    # virada de ano
        (date(2026, 1, 31), 31, date(2026, 1, 31)),
        (date(2026, 2, 28), 31, date(2026, 2, 28)),   # RB-021: fevereiro fecha no dia 28
        (date(2026, 3, 1), 31, date(2026, 3, 31)),
        (date(2028, 2, 29), 30, date(2028, 2, 29)),   # bissexto
    ],
)
def test_invoice_closing_for_purchase(purchase, closing_day, expected):
    assert cycle.invoice_closing_for(purchase, closing_day) == expected


@pytest.mark.parametrize(
    ("closing", "due_day", "expected"),
    [
        (date(2026, 10, 5), 12, date(2026, 10, 12)),   # vence no mesmo mês
        (date(2026, 10, 28), 5, date(2026, 11, 5)),    # vence no mês seguinte
        (date(2026, 10, 5), 5, date(2026, 11, 5)),     # mesmo dia: estritamente depois
        (date(2026, 12, 20), 3, date(2027, 1, 3)),     # virada de ano
        (date(2026, 1, 31), 31, date(2026, 2, 28)),    # RB-021 no vencimento
    ],
)
def test_due_date_is_first_due_day_after_closing(closing, due_day, expected):
    assert cycle.due_date_for(closing, due_day) == expected


def test_period_covers_day_after_previous_closing_through_closing():
    assert cycle.period_start(date(2026, 10, 5), 5) == date(2026, 9, 6)
    assert cycle.period_start(date(2026, 3, 31), 31) == date(2026, 3, 1)  # fev fechou dia 28
    assert cycle.period_start(date(2027, 1, 5), 5) == date(2026, 12, 6)


def test_every_day_belongs_to_exactly_one_invoice_and_inside_its_period():
    """Propriedade: os períodos cobrem o calendário sem buraco nem sobreposição."""
    for closing_day in (1, 5, 28, 29, 30, 31):
        day = date(2026, 1, 1)
        while day <= date(2027, 3, 1):
            closing = cycle.invoice_closing_for(day, closing_day)
            assert cycle.is_valid_closing_date(closing, closing_day)
            assert cycle.period_start(closing, closing_day) <= day <= closing, (closing_day, day)
            day = date.fromordinal(day.toordinal() + 1)


def test_shift_closing_walks_months_and_keeps_the_clamped_day():
    start = date(2026, 1, 31)

    assert [cycle.shift_closing(start, n, 31) for n in range(4)] == [
        date(2026, 1, 31), date(2026, 2, 28), date(2026, 3, 31), date(2026, 4, 30),
    ]
    assert cycle.shift_closing(date(2026, 3, 31), -1, 31) == date(2026, 2, 28)


def test_valid_closing_dates():
    assert cycle.is_valid_closing_date(date(2026, 2, 28), 31)
    assert not cycle.is_valid_closing_date(date(2026, 2, 27), 31)
    assert not cycle.is_valid_closing_date(date(2026, 10, 6), 5)


def test_status_future_when_period_has_not_started():
    closing = date(2026, 12, 5)  # período de 06/11 a 05/12

    status = cycle.invoice_status(
        closing, date(2026, 12, 12), cycle.period_start(closing, 5), Decimal("100"), date(2026, 9, 1)
    )

    assert status == "future"


def test_status_progression_over_time():
    closing, due = date(2026, 10, 5), date(2026, 10, 12)
    start = cycle.period_start(closing, 5)
    status = lambda today, balance: cycle.invoice_status(closing, due, start, Decimal(balance), today)  # noqa: E731

    assert status(date(2026, 9, 5), "100") == "future"
    assert status(date(2026, 9, 6), "100") == "open"
    assert status(date(2026, 10, 5), "100") == "open"      # dia do fechamento ainda acumula
    assert status(date(2026, 10, 6), "100") == "closed"
    assert status(date(2026, 10, 12), "100") == "closed"   # vence hoje ainda não é vencida
    assert status(date(2026, 10, 13), "100") == "overdue"
    assert status(date(2026, 10, 13), "0") == "paid"
    assert status(date(2026, 10, 6), "-20") == "paid"      # estorno maior que o total


@pytest.mark.parametrize(("total", "count"), [("100.00", 3), ("0.05", 3), ("999.99", 12), ("10.00", 1)])
def test_split_amount_sums_to_total_with_leftover_on_first(total, count):
    parts = cycle.split_amount(Decimal(total), count)

    assert sum(parts) == Decimal(total)
    assert parts[0] >= parts[-1]
    assert len(parts) == count
