"""Calculadora de cronograma de dívidas (RF-033/RF-040). Funções puras, sem banco.

Taxa em fração mensal (0.0199 = 1,99% a.m.). Tudo em centavos; a última parcela absorve o
arredondamento, então a soma do principal é sempre exatamente o saldo de partida.
"""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")
ZERO = Decimal("0.00")
MAX_ROWS = 600

SYSTEMS = ("price", "sac", "zero")


class ScheduleError(Exception):
    """Parâmetros que não geram um cronograma válido (ex: parcela que não cobre os juros)."""


@dataclass(frozen=True)
class Row:
    number: int  # 1-based dentro do cronograma gerado
    principal: Decimal
    interest: Decimal
    payment: Decimal
    balance: Decimal  # saldo devedor DEPOIS desta parcela


def money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def _interest(balance: Decimal, rate: Decimal) -> Decimal:
    return money(balance * rate)


def price_payment(principal: Decimal, rate: Decimal, count: int) -> Decimal:
    """PMT = P·i / (1 − (1+i)^−n); com i = 0 são n parcelas iguais."""
    if rate == 0:
        return money(principal / count)
    factor = (Decimal(1) + rate) ** (-count)
    return money(principal * rate / (Decimal(1) - factor))


def build(principal: Decimal, system: str, rate: Decimal, count: int) -> list[Row]:
    """Cronograma completo de `count` parcelas. `zero` ignora a taxa."""
    if system not in SYSTEMS:
        raise ScheduleError(f"sistema invalido: {system}")
    if principal <= 0 or count < 1:
        raise ScheduleError("principal e numero de parcelas precisam ser positivos")
    if system == "zero":
        rate = Decimal(0)

    rows: list[Row] = []
    balance = money(principal)
    payment = price_payment(principal, rate, count) if system in ("price", "zero") else None
    amortization = money(principal / count) if system == "sac" else None

    for number in range(1, count + 1):
        interest = _interest(balance, rate)
        if number == count:
            part = balance
        elif payment is not None:
            part = min(payment - interest, balance)
        else:
            part = min(amortization, balance)
        if part < 0:
            raise ScheduleError("a parcela nao cobre os juros")
        balance = money(balance - part)
        rows.append(Row(number, part, interest, part + interest, balance))
    return rows


def fixed_payment(balance: Decimal, rate: Decimal, payment: Decimal) -> list[Row]:
    """Mantém a parcela e deixa o prazo cair (Price, 'reduzir prazo'): a última parcela fica menor."""
    if balance <= 0:
        return []
    if payment <= balance * rate:
        raise ScheduleError("a parcela nao cobre os juros do saldo")
    rows: list[Row] = []
    remaining = money(balance)
    number = 0
    while remaining > 0:
        number += 1
        if number > MAX_ROWS:
            raise ScheduleError("o prazo restante passa de 600 parcelas")
        interest = _interest(remaining, rate)
        part = min(payment - interest, remaining)
        if part <= 0:
            raise ScheduleError("a parcela nao cobre os juros do saldo")
        remaining = money(remaining - part)
        rows.append(Row(number, part, interest, part + interest, remaining))
    return rows


def constant_amortization(balance: Decimal, rate: Decimal, amortization: Decimal) -> list[Row]:
    """Mantém a amortização do SAC e deixa o prazo cair ('reduzir prazo')."""
    if balance <= 0:
        return []
    if amortization <= 0:
        raise ScheduleError("amortizacao precisa ser positiva")
    rows: list[Row] = []
    remaining = money(balance)
    number = 0
    while remaining > 0:
        number += 1
        if number > MAX_ROWS:
            raise ScheduleError("o prazo restante passa de 600 parcelas")
        interest = _interest(remaining, rate)
        part = min(amortization, remaining)
        remaining = money(remaining - part)
        rows.append(Row(number, part, interest, part + interest, remaining))
    return rows
