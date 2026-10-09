"""Saldos por conta e DRE (RF-031, RF-033).

Slice de leitura: consome só os `service` públicos das outras slices, como o dashboard.
"""

import uuid
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from src.features.accounts import service as accounts_service
from src.features.accounts.models import AccountType
from src.features.categories import service as categories_service
from src.features.commitments import service as commitments_service
from src.features.commitments.models import CommitmentDirection
from src.features.transactions import service as transactions_service
from src.features.transactions.models import TransactionType
from src.features.transfers import service as transfers_service

ZERO = Decimal("0.00")
CENT = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    return Decimal(value).quantize(CENT)


# ---------- saldos por conta ----------

@dataclass(frozen=True)
class AccountBalance:
    account_id: uuid.UUID
    name: str
    type: AccountType
    is_archived: bool
    opening_balance: Decimal
    balance: Decimal  # positivo = dinheiro; num cartão, negativo = dívida


@dataclass(frozen=True)
class Balances:
    accounts: list[AccountBalance]
    cash_total: Decimal  # soma das contas que NÃO são cartão (inclui arquivadas)
    card_debt_total: Decimal


def balances(db: Session, user_id: uuid.UUID, today: date | None = None) -> Balances:
    """RB-026: saldo = inicial + receitas − despesas + transferências recebidas − enviadas.
    Só conta o que já aconteceu (data ≤ hoje); lançamento futuro ainda não mexeu no saldo."""
    today = today or date.today()
    delta: dict[uuid.UUID, Decimal] = {}

    for transaction in transactions_service.list_transactions(db, user_id):
        if transaction.occurred_at > today:
            continue
        signed = transaction.amount if transaction.type == TransactionType.INCOME else -transaction.amount
        delta[transaction.account_id] = delta.get(transaction.account_id, ZERO) + signed

    for transfer in transfers_service.list_transfers(db, user_id, end_date=today):
        delta[transfer.from_account_id] = delta.get(transfer.from_account_id, ZERO) - transfer.amount
        delta[transfer.to_account_id] = delta.get(transfer.to_account_id, ZERO) + transfer.amount

    rows = [
        AccountBalance(
            account_id=account.id,
            name=account.name,
            type=account.type,
            is_archived=account.is_archived,
            opening_balance=money(account.opening_balance),
            balance=money(account.opening_balance + delta.get(account.id, ZERO)),
        )
        for account in accounts_service.list_accounts(db, user_id)
    ]
    cash = sum((r.balance for r in rows if r.type != AccountType.CREDIT_CARD), ZERO)
    debt = sum((-r.balance for r in rows if r.type == AccountType.CREDIT_CARD), ZERO)
    return Balances(accounts=rows, cash_total=money(cash), card_debt_total=money(debt))


# ---------- DRE ----------

REVENUE_SIDE = ("revenue", "financial_revenue")
COST_SIDE = ("deduction", "variable_expense", "fixed_expense", "financial_expense")

GROUP_LABELS = {
    "revenue": "Receitas",
    "deduction": "Deduções",
    "variable_expense": "Despesas variáveis",
    "fixed_expense": "Despesas fixas",
    "financial_expense": "Despesas financeiras",
    "financial_revenue": "Receitas financeiras",
}


@dataclass
class CategoryAmount:
    category_id: uuid.UUID | None
    name: str
    amount: Decimal


@dataclass
class DreLine:
    key: str
    label: str
    kind: str  # "group" | "subtotal" | "ungrouped"
    amount: Decimal
    previous_amount: Decimal
    percent_of_net_revenue: Decimal | None
    categories: list[CategoryAmount] = field(default_factory=list)


@dataclass
class Dre:
    start_date: date
    end_date: date
    previous_start_date: date
    previous_end_date: date
    include_forecast: bool
    lines: list[DreLine]
    net_result: Decimal
    previous_net_result: Decimal
    ungrouped_count: int  # categorias com movimento e sem grupo, para avisar (RB-028)


@dataclass
class _Totals:
    groups: dict[str, Decimal]
    by_category: dict[tuple[str | None, uuid.UUID], Decimal]
    ungrouped_income: Decimal
    ungrouped_expense: Decimal


def _collect(
    db: Session,
    user_id: uuid.UUID,
    start: date,
    end: date,
    include_forecast: bool,
    category_groups: dict[uuid.UUID, str | None],
) -> _Totals:
    totals = _Totals(groups={g: ZERO for g in GROUP_LABELS}, by_category={}, ungrouped_income=ZERO, ungrouped_expense=ZERO)

    def add(category_id: uuid.UUID, kind: TransactionType, amount: Decimal) -> None:
        group = category_groups.get(category_id)
        if group is None:
            bucket = "ungrouped_income" if kind == TransactionType.INCOME else "ungrouped_expense"
            if kind == TransactionType.INCOME:
                totals.ungrouped_income += amount
            else:
                totals.ungrouped_expense += amount
            key = (bucket, category_id)
            totals.by_category[key] = totals.by_category.get(key, ZERO) + amount
            return

        # RB-029: lançamento no sentido oposto ao do grupo abate o total do grupo.
        same_direction = (kind == TransactionType.INCOME) == (group in REVENUE_SIDE)
        signed = amount if same_direction else -amount
        totals.groups[group] += signed
        key = (group, category_id)
        totals.by_category[key] = totals.by_category.get(key, ZERO) + signed

    # Competência: data do lançamento; transferências nunca aparecem aqui (RB-014/RB-022).
    for transaction in transactions_service.list_transactions(db, user_id, start, end):
        add(transaction.category_id, transaction.type, transaction.amount)

    if include_forecast:
        # "Incluir previsto": contas a pagar/receber ainda em aberto, pelo vencimento (saldo restante).
        views, _ = commitments_service.list_commitments(db, user_id, status="pending", due_from=start, due_to=end)
        for view in views:
            kind = (
                TransactionType.EXPENSE
                if view.commitment.direction == CommitmentDirection.PAYABLE
                else TransactionType.INCOME
            )
            add(view.commitment.category_id, kind, view.balance)

    return totals


def _results(t: _Totals) -> dict[str, Decimal]:
    g = t.groups
    net_revenue = g["revenue"] - g["deduction"]
    gross_result = net_revenue - g["variable_expense"]
    operating_result = gross_result - g["fixed_expense"]
    net_result = (
        operating_result - g["financial_expense"] + g["financial_revenue"] + t.ungrouped_income - t.ungrouped_expense
    )
    return {
        "net_revenue": net_revenue,
        "gross_result": gross_result,
        "operating_result": operating_result,
        "net_result": net_result,
    }


def dre(
    db: Session,
    user_id: uuid.UUID,
    start_date: date,
    end_date: date,
    include_forecast: bool = False,
) -> Dre:
    """RF-033: DRE do período, por competência, comparado com o período imediatamente anterior."""
    categories = categories_service.list_categories(db, user_id)
    names = {c.id: c.name for c in categories}
    groups = {c.id: c.dre_group for c in categories}

    length = (end_date - start_date).days + 1
    previous_end = start_date - timedelta(days=1)
    previous_start = previous_end - timedelta(days=length - 1)

    current = _collect(db, user_id, start_date, end_date, include_forecast, groups)
    previous = _collect(db, user_id, previous_start, previous_end, include_forecast, groups)
    cur_r, prev_r = _results(current), _results(previous)
    net_revenue = cur_r["net_revenue"]

    def pct(value: Decimal) -> Decimal | None:
        if net_revenue <= 0:
            return None
        return (value / net_revenue * 100).quantize(CENT)

    def categories_of(group: str | None) -> list[CategoryAmount]:
        rows = [
            CategoryAmount(category_id=cid, name=names.get(cid, "?"), amount=money(amount))
            for (g, cid), amount in current.by_category.items()
            if g == group and amount != 0
        ]
        return sorted(rows, key=lambda r: abs(r.amount), reverse=True)

    def group_line(group: str) -> DreLine:
        return DreLine(
            key=group,
            label=GROUP_LABELS[group],
            kind="group",
            amount=money(current.groups[group]),
            previous_amount=money(previous.groups[group]),
            percent_of_net_revenue=pct(current.groups[group]),
            categories=categories_of(group),
        )

    def subtotal(key: str, label: str) -> DreLine:
        return DreLine(
            key=key,
            label=label,
            kind="subtotal",
            amount=money(cur_r[key]),
            previous_amount=money(prev_r[key]),
            percent_of_net_revenue=pct(cur_r[key]),
        )

    ungrouped_income = DreLine(
        key="ungrouped_income",
        label="Receitas sem grupo",
        kind="ungrouped",
        amount=money(current.ungrouped_income),
        previous_amount=money(previous.ungrouped_income),
        percent_of_net_revenue=pct(current.ungrouped_income),
        categories=categories_of("ungrouped_income"),
    )
    ungrouped_expense = DreLine(
        key="ungrouped_expense",
        label="Despesas sem grupo",
        kind="ungrouped",
        amount=money(current.ungrouped_expense),
        previous_amount=money(previous.ungrouped_expense),
        percent_of_net_revenue=pct(current.ungrouped_expense),
        categories=categories_of("ungrouped_expense"),
    )
    lines = [
        group_line("revenue"),
        group_line("deduction"),
        subtotal("net_revenue", "Receita líquida"),
        group_line("variable_expense"),
        subtotal("gross_result", "Resultado bruto"),
        group_line("fixed_expense"),
        subtotal("operating_result", "Resultado operacional"),
        group_line("financial_expense"),
        group_line("financial_revenue"),
        ungrouped_income,
        ungrouped_expense,
        subtotal("net_result", "Resultado do período"),
    ]

    return Dre(
        start_date=start_date,
        end_date=end_date,
        previous_start_date=previous_start,
        previous_end_date=previous_end,
        include_forecast=include_forecast,
        lines=lines,
        net_result=money(cur_r["net_result"]),
        previous_net_result=money(prev_r["net_result"]),
        ungrouped_count=len(ungrouped_income.categories) + len(ungrouped_expense.categories),
    )
