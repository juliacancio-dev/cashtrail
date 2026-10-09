"""Fluxo de caixa mensal, previsto × realizado, com projeção (RF-034, RF-035, RF-036).

Regime de CAIXA (RB-023): conta quando o dinheiro se move. Contas de caixa são as que não
são cartão; o cartão é dívida. Cada item tem uma coluna:

- realized: movimento que já aconteceu (data ≤ hoje).
- planned:  valor bruto na data de vencimento/previsão (RB-024), mesmo que já tenha sido pago.
            `remaining` é o que ainda vai acontecer, e `projected_when` onde isso cai
            (item vencido e não pago é tratado como pendente hoje, RB-025).

A projeção de um mês = realizado do mês + o que resta dos itens previstos naquele mês.
"""

import calendar
import uuid
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from src.features.accounts import service as accounts_service
from src.features.accounts.models import NON_CASH_TYPES, AccountType
from src.features.categories import service as categories_service
from src.features.commitments import service as commitments_service
from src.features.commitments.models import CommitmentDirection
from src.features.credit_cards import service as credit_cards_service
from src.features.recurring import service as recurring_service
from src.features.transactions import service as transactions_service
from src.features.transactions.models import TransactionType
from src.features.transfers import service as transfers_service

ZERO = Decimal("0.00")
CENT = Decimal("0.01")
MAX_MONTHS = 24
INVOICE_LIMIT = 120

SOURCES = ("transactions", "transfers", "commitments", "card_invoices", "recurring")


def money(value: Decimal) -> Decimal:
    return Decimal(value).quantize(CENT)


@dataclass
class FlowItem:
    column: str  # "realized" | "planned"
    direction: str  # "in" | "out"
    when: date
    amount: Decimal
    source: str
    description: str
    category_id: uuid.UUID | None = None
    category_name: str | None = None
    ref_id: uuid.UUID | None = None
    remaining: Decimal = ZERO
    projected_when: date | None = None


@dataclass
class SourceTotals:
    planned_in: Decimal = ZERO
    planned_out: Decimal = ZERO
    realized_in: Decimal = ZERO
    realized_out: Decimal = ZERO


@dataclass
class CashFlowMonth:
    month: str  # "YYYY-MM"
    status: str  # "past" | "current" | "future"
    opening_balance: Decimal  # saldo projetado no início do mês
    planned_in: Decimal
    planned_out: Decimal
    realized_in: Decimal
    realized_out: Decimal
    projected_in: Decimal
    projected_out: Decimal
    closing_projected: Decimal
    closing_realized: Decimal | None  # None em mês futuro
    variance_in: Decimal  # realizado − previsto
    variance_out: Decimal
    sources: dict[str, SourceTotals] = field(default_factory=dict)


@dataclass
class CashFlow:
    start_month: str
    months: list[CashFlowMonth]
    cash_balance_today: Decimal
    # Itens que o fluxo NÃO enxerga e podem fazer o saldo real ficar abaixo do projetado.
    warnings: list[str]


# ---------- calendário ----------

def first_of_month(day: date) -> date:
    return day.replace(day=1)


def add_months(first: date, months: int) -> date:
    index = first.month - 1 + months
    return date(first.year + index // 12, index % 12 + 1, 1)


def last_of_month(first: date) -> date:
    return first.replace(day=calendar.monthrange(first.year, first.month)[1])


def month_key(day: date) -> str:
    return f"{day.year:04d}-{day.month:02d}"


# ---------- coleta ----------

def collect_items(db: Session, user_id: uuid.UUID, today: date, horizon_end: date) -> list[FlowItem]:
    accounts = accounts_service.list_accounts(db, user_id)
    account_names = {a.id: a.name for a in accounts}
    cash_ids = {a.id for a in accounts if a.type not in NON_CASH_TYPES}
    card_ids = {a.id for a in accounts if a.type == AccountType.CREDIT_CARD}
    loan_ids = {a.id for a in accounts if a.type == AccountType.LOAN}
    category_names = {c.id: c.name for c in categories_service.list_categories(db, user_id)}
    items: list[FlowItem] = []

    def name_of(category_id: uuid.UUID | None) -> str | None:
        return category_names.get(category_id) if category_id else None

    # 1) Lançamentos em contas de caixa. Compra no cartão NÃO entra aqui (RB-023): só o pagamento.
    for t in transactions_service.list_transactions(db, user_id):
        if t.account_id not in cash_ids:
            continue
        direction = "in" if t.type == TransactionType.INCOME else "out"
        description = t.description or name_of(t.category_id) or "(sem descrição)"
        if t.occurred_at <= today:
            items.append(
                FlowItem("realized", direction, t.occurred_at, t.amount, "transactions", description,
                         t.category_id, name_of(t.category_id), t.id)
            )
        elif t.occurred_at <= horizon_end:
            # Data futura: ainda não aconteceu, entra como previsto.
            items.append(
                FlowItem("planned", direction, t.occurred_at, t.amount, "transactions", description,
                         t.category_id, name_of(t.category_id), t.id, remaining=t.amount, projected_when=t.occurred_at)
            )

    # 2) Transferências que cruzam a fronteira caixa ↔ cartão (RB-023).
    for tr in transfers_service.list_transfers(db, user_id):
        from_cash, to_cash = tr.from_account_id in cash_ids, tr.to_account_id in cash_ids
        if from_cash == to_cash:
            continue  # entre contas de caixa (ou entre cartões): movimento interno
        if from_cash:
            kind = "Pagamento de dívida" if tr.to_account_id in loan_ids else "Pagamento de cartão"
            description = tr.description or f"{kind}: {account_names.get(tr.to_account_id, '?')}"
            items.append(FlowItem("realized", "out", tr.occurred_at, tr.amount, "transfers", description, ref_id=tr.id))
        else:
            kind = "Recebido da dívida" if tr.from_account_id in loan_ids else "Recebido do cartão"
            description = tr.description or f"{kind}: {account_names.get(tr.from_account_id, '?')}"
            items.append(FlowItem("realized", "in", tr.occurred_at, tr.amount, "transfers", description, ref_id=tr.id))

    # 3) Contas a pagar e a receber: previsto pelo bruto no vencimento (RB-024).
    views, _ = commitments_service.list_commitments(db, user_id, today=today)
    for view in views:
        c = view.commitment
        if view.status == "canceled":
            continue
        description = c.description
        if c.installment_number and c.installment_count:
            description = f"{description} ({c.installment_number}/{c.installment_count})"
        remaining = view.balance if view.balance > 0 else ZERO
        items.append(
            FlowItem(
                "planned",
                "out" if c.direction == CommitmentDirection.PAYABLE else "in",
                c.due_date,
                c.amount,
                "commitments",
                description,
                c.category_id,
                name_of(c.category_id),
                c.id,
                remaining=remaining,
                projected_when=max(c.due_date, today) if remaining > 0 else None,
            )
        )

    # 4) Faturas de cartão: o gasto vira saída no vencimento da fatura.
    for card_view in credit_cards_service.list_cards(db, user_id):
        for invoice in credit_cards_service.list_invoices(
            db, user_id, card_view.card.id, today=today, limit=INVOICE_LIMIT
        ):
            if invoice.total <= 0:
                continue
            remaining = invoice.balance if invoice.balance > 0 else ZERO
            items.append(
                FlowItem(
                    "planned",
                    "out",
                    invoice.due_date,
                    invoice.total,
                    "card_invoices",
                    f"Fatura {card_view.account_name} {invoice.closing_date:%m/%Y}",
                    ref_id=card_view.card.id,
                    remaining=remaining,
                    projected_when=max(invoice.due_date, today) if remaining > 0 else None,
                )
            )

    # 5) Recorrências futuras, expandidas pela regra (decisão 4). Numa conta de cartão, o
    # dinheiro só sai no vencimento da fatura daquele ciclo.
    for occ in recurring_service.list_future_occurrences(db, user_id, horizon_end):
        direction = "in" if occ.type == TransactionType.INCOME else "out"
        description = f"{occ.description or name_of(occ.category_id) or 'Recorrência'} (recorrência)"
        when = occ.occurs_on
        if occ.account_id in card_ids:
            due = credit_cards_service.due_date_for_purchase(db, user_id, occ.account_id, occ.occurs_on)
            if due is None:
                continue
            when = due
        projected = max(when, today)
        if projected > horizon_end:
            continue
        items.append(
            FlowItem("planned", direction, when, occ.amount, "recurring", description,
                     occ.category_id, name_of(occ.category_id), occ.recurring_id,
                     remaining=occ.amount, projected_when=projected)
        )

    return items


def _opening_total(db: Session, user_id: uuid.UUID) -> Decimal:
    return sum(
        (a.opening_balance for a in accounts_service.list_accounts(db, user_id) if a.type not in NON_CASH_TYPES),
        ZERO,
    )


# ---------- montagem ----------

def parse_month(value: str) -> date:
    year, month = value.split("-")
    return date(int(year), int(month), 1)


def build_cash_flow(
    db: Session,
    user_id: uuid.UUID,
    start_month: date,
    months: int,
    today: date | None = None,
) -> CashFlow:
    today = today or date.today()
    months = max(1, min(months, MAX_MONTHS))
    start_month = first_of_month(start_month)
    current = first_of_month(today)
    requested_last = add_months(start_month, months - 1)

    # A cadeia de saldos começa no primeiro mês relevante (o passado ou o mês atual) e vai
    # até o último pedido; assim o saldo projetado de um mês futuro nunca ignora o que
    # acontece entre hoje e a janela pedida.
    chain_first = min(start_month, current)
    chain_last = max(requested_last, current)
    horizon_end = last_of_month(chain_last)

    items = collect_items(db, user_id, today, horizon_end)
    opening_total = _opening_total(db, user_id)

    realized = [i for i in items if i.column == "realized"]
    planned = [i for i in items if i.column == "planned"]

    def realized_net_before(day: date) -> Decimal:
        return sum(
            ((i.amount if i.direction == "in" else -i.amount) for i in realized if i.when < day),
            ZERO,
        )

    results: dict[date, CashFlowMonth] = {}
    projected_opening = opening_total + realized_net_before(chain_first)
    cursor = chain_first
    while cursor <= chain_last:
        month_start, month_end = cursor, last_of_month(cursor)

        def inside(day: date | None) -> bool:
            return day is not None and month_start <= day <= month_end

        def total(rows: list[FlowItem], direction: str, *, remaining: bool = False) -> Decimal:
            """Soma por sentido; `remaining` usa o que resta e a data em que isso cai."""
            if remaining:
                return sum(
                    (r.remaining for r in rows if r.direction == direction and r.remaining > 0 and inside(r.projected_when)),
                    ZERO,
                )
            return sum((r.amount for r in rows if r.direction == direction and inside(r.when)), ZERO)

        r_in, r_out = total(realized, "in"), total(realized, "out")
        p_in, p_out = total(planned, "in"), total(planned, "out")
        rem_in, rem_out = total(planned, "in", remaining=True), total(planned, "out", remaining=True)
        proj_in, proj_out = r_in + rem_in, r_out + rem_out
        status = "past" if cursor < current else "current" if cursor == current else "future"
        realized_opening = opening_total + realized_net_before(cursor)

        sources: dict[str, SourceTotals] = {}
        for item in items:
            if not inside(item.when):
                continue
            bucket = sources.setdefault(item.source, SourceTotals())
            if item.column == "realized":
                if item.direction == "in":
                    bucket.realized_in += item.amount
                else:
                    bucket.realized_out += item.amount
            elif item.direction == "in":
                bucket.planned_in += item.amount
            else:
                bucket.planned_out += item.amount

        results[cursor] = CashFlowMonth(
            month=month_key(cursor),
            status=status,
            opening_balance=money(projected_opening),
            planned_in=money(p_in),
            planned_out=money(p_out),
            realized_in=money(r_in),
            realized_out=money(r_out),
            projected_in=money(proj_in),
            projected_out=money(proj_out),
            closing_projected=money(projected_opening + proj_in - proj_out),
            closing_realized=money(realized_opening + r_in - r_out) if status != "future" else None,
            variance_in=money(r_in - p_in),
            variance_out=money(r_out - p_out),
            sources=sources,
        )
        projected_opening = projected_opening + proj_in - proj_out
        cursor = add_months(cursor, 1)

    window = []
    cursor = start_month
    while cursor <= requested_last:
        window.append(results[cursor])
        cursor = add_months(cursor, 1)

    return CashFlow(
        start_month=month_key(start_month),
        months=window,
        cash_balance_today=money(opening_total + realized_net_before(today + timedelta(days=1))),
        warnings=[
            "A projeção não inclui compras futuras no cartão que ainda não foram lançadas: "
            "o saldo real pode ficar abaixo do projetado."
        ],
    )


def month_items(
    db: Session,
    user_id: uuid.UUID,
    month_first: date,
    column: str,
    direction: str,
    today: date | None = None,
) -> list[FlowItem]:
    """RF-036: os itens que compõem um número do fluxo (colunas planned, realized ou projected)."""
    today = today or date.today()
    month_first = first_of_month(month_first)
    month_end = last_of_month(month_first)
    items = collect_items(db, user_id, today, max(month_end, last_of_month(first_of_month(today))))

    def inside(day: date | None) -> bool:
        return day is not None and month_first <= day <= month_end

    selected: list[FlowItem] = []
    for item in items:
        if item.direction != direction:
            continue
        if column == "realized" and item.column == "realized" and inside(item.when):
            selected.append(item)
        elif column == "planned" and item.column == "planned" and inside(item.when):
            selected.append(item)
        elif column == "projected":
            if item.column == "realized" and inside(item.when):
                selected.append(item)
            elif item.column == "planned" and item.remaining > 0 and inside(item.projected_when):
                # No projetado entra só o que resta, na data em que vai cair.
                selected.append(
                    FlowItem("planned", item.direction, item.projected_when, item.remaining, item.source,
                             item.description, item.category_id, item.category_name, item.ref_id)
                )
    return sorted(selected, key=lambda i: (i.when, i.description))
