"""Calendário do dinheiro: saldo em caixa dia a dia de um mês (Marco 16, doc 32, decisão 4).

Reaproveita os itens do fluxo de caixa (`cash_flow.collect_items`), sem regra nova:

- realizado: entra no dia em que aconteceu;
- previsto: entra só o que resta, no dia em que vai cair (vencido e não pago cai hoje).

Saldo no fim do dia d = saldo inicial das contas de caixa
                         + realizados com data ≤ d
                         + o que resta dos previstos com data entre hoje e d.
"""

import math
import uuid
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from src.features.reports.cash_flow import (
    ZERO,
    FlowItem,
    _opening_total,
    collect_items,
    first_of_month,
    last_of_month,
    money,
)


@dataclass
class CalendarEvent:
    kind: str  # "realized" | "planned"
    direction: str  # "in" | "out"
    amount: Decimal
    source: str
    description: str
    category_name: str | None


@dataclass
class CalendarDay:
    day: date
    status: str  # "past" | "today" | "future"
    balance: Decimal  # saldo em caixa no fim do dia
    net: Decimal
    is_tight: bool
    events: list[CalendarEvent] = field(default_factory=list)


@dataclass
class MoneyCalendar:
    month: str  # "YYYY-MM"
    today: date
    cash_today: Decimal  # só o realizado até hoje: igual ao cash_total de /reports/balances
    opening_balance: Decimal  # saldo no fim da véspera do dia 1
    closing_balance: Decimal
    tightest_day: date
    tightest_balance: Decimal
    days: list[CalendarDay]


def _signed(direction: str, amount: Decimal) -> Decimal:
    return amount if direction == "in" else -amount


def _dated_events(items: list[FlowItem], today: date) -> list[tuple[date, CalendarEvent]]:
    """Cada item vira um evento no dia em que mexe no caixa."""
    events: list[tuple[date, CalendarEvent]] = []
    for item in items:
        if item.column == "realized":
            events.append((item.when, CalendarEvent("realized", item.direction, item.amount, item.source,
                                                    item.description, item.category_name)))
        elif item.remaining > 0 and item.projected_when is not None and item.projected_when >= today:
            events.append((item.projected_when, CalendarEvent("planned", item.direction, item.remaining,
                                                              item.source, item.description, item.category_name)))
    return events


def _tight_days(balances: list[Decimal]) -> set[int]:
    """Dia apertado = saldo no quarto mais baixo do mês (decisão 6). Mês sem variação não tem.

    Se os empates no valor de corte passariam de um quarto do mês (um saldo parado por
    semanas), só entram os dias abaixo dele: marcar o mês quase inteiro não diz nada.
    """
    if not balances or min(balances) == max(balances):
        return set()
    quarter = math.ceil(len(balances) / 4)
    threshold = sorted(balances)[quarter - 1]
    tight = {i for i, b in enumerate(balances) if b <= threshold}
    if len(tight) > quarter:
        tight = {i for i, b in enumerate(balances) if b < threshold}
    return tight


def build_calendar(db: Session, user_id: uuid.UUID, month: date, today: date | None = None) -> MoneyCalendar:
    today = today or date.today()
    first = first_of_month(month)
    last = last_of_month(first)
    items = collect_items(db, user_id, today, max(last, today))
    events = _dated_events(items, today)

    running = _opening_total(db, user_id) + sum((_signed(e.direction, e.amount) for d, e in events if d < first), ZERO)
    opening = running
    by_day: dict[date, list[CalendarEvent]] = {}
    for d, e in events:
        if first <= d <= last:
            by_day.setdefault(d, []).append(e)

    days: list[CalendarDay] = []
    cursor = first
    while cursor <= last:
        day_events = sorted(by_day.get(cursor, []), key=lambda e: (e.kind, e.description))
        net = sum((_signed(e.direction, e.amount) for e in day_events), ZERO)
        running += net
        status = "past" if cursor < today else "today" if cursor == today else "future"
        days.append(CalendarDay(cursor, status, money(running), money(net), False, day_events))
        cursor += timedelta(days=1)

    for i in _tight_days([d.balance for d in days]):
        days[i].is_tight = True
    tightest = min(days, key=lambda d: d.balance)  # min devolve o primeiro em caso de empate

    cash_today = _opening_total(db, user_id) + sum(
        (_signed(e.direction, e.amount) for d, e in events if e.kind == "realized" and d <= today), ZERO
    )
    return MoneyCalendar(
        month=f"{first:%Y-%m}",
        today=today,
        cash_today=money(cash_today),
        opening_balance=money(opening),
        closing_balance=days[-1].balance,
        tightest_day=tightest.day,
        tightest_balance=tightest.balance,
        days=days,
    )
