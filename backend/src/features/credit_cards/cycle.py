"""Matemática do ciclo de fatura do cartão (RB-019, RB-021). Funções puras, sem banco.

Uma fatura é identificada pela sua DATA DE FECHAMENTO. O fechamento de cada mês é o
`closing_day` daquele mês, ajustado para o último dia quando o mês é mais curto (RB-021).
"""

import calendar
from datetime import date, timedelta
from decimal import Decimal


def clamp_day(year: int, month: int, day: int) -> date:
    """Dia `day` do mês, ou o último dia do mês se ele não existir (29 a 31)."""
    return date(year, month, min(day, calendar.monthrange(year, month)[1]))


def add_months(base: date, months: int) -> date:
    month_index = base.month - 1 + months
    return clamp_day(base.year + month_index // 12, month_index % 12 + 1, base.day)


def closing_date_in_month(year: int, month: int, closing_day: int) -> date:
    return clamp_day(year, month, closing_day)


def shift_closing(closing_date: date, months: int, closing_day: int) -> date:
    """Fechamento `months` meses depois (ou antes, se negativo) de outro fechamento."""
    month_index = closing_date.month - 1 + months
    return closing_date_in_month(closing_date.year + month_index // 12, month_index % 12 + 1, closing_day)


def is_valid_closing_date(closing_date: date, closing_day: int) -> bool:
    return closing_date == closing_date_in_month(closing_date.year, closing_date.month, closing_day)


def invoice_closing_for(purchase_date: date, closing_day: int) -> date:
    """RB-019: a compra entra na fatura que fecha na primeira data de fechamento >= à compra
    (no dia do fechamento, inclusive, ela ainda entra na fatura que fecha)."""
    this_month = closing_date_in_month(purchase_date.year, purchase_date.month, closing_day)
    if purchase_date <= this_month:
        return this_month
    return shift_closing(this_month, 1, closing_day)


def period_start(closing_date: date, closing_day: int) -> date:
    """Primeiro dia coberto pela fatura: o dia seguinte ao fechamento anterior."""
    return shift_closing(closing_date, -1, closing_day) + timedelta(days=1)


def due_date_for(closing_date: date, due_day: int) -> date:
    """Vencimento: a primeira data DEPOIS do fechamento cujo dia é `due_day` (ajustado ao mês)."""
    candidate = clamp_day(closing_date.year, closing_date.month, due_day)
    if candidate > closing_date:
        return candidate
    month_index = closing_date.month  # mês seguinte (0-based = month)
    return clamp_day(closing_date.year + month_index // 12, month_index % 12 + 1, due_day)


def invoice_status(closing_date: date, due_date: date, start: date, balance: Decimal, today: date) -> str:
    """future (ainda não começou) · open (acumulando; inclui o dia do fechamento) ·
    closed (fechou, a vencer) · overdue (venceu com saldo) · paid (fechou e zerou)."""
    if start > today:
        return "future"
    if today <= closing_date:
        return "open"
    if balance <= 0:
        return "paid"
    if due_date < today:
        return "overdue"
    return "closed"


def split_amount(total: Decimal, count: int) -> list[Decimal]:
    """A soma das parcelas é sempre o total; os centavos que sobram vão na primeira."""
    cents = int((total * 100).to_integral_value())
    base, remainder = divmod(cents, count)
    values = [base] * count
    values[0] += remainder
    return [(Decimal(value) / 100).quantize(Decimal("0.01")) for value in values]
