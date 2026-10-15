"""Balanço patrimonial pessoal (Marco 12): ativos − passivos = patrimônio líquido.

Somente leitura. O saldo de cada conta numa data vem de `balances` (histórico é a fonte da
verdade, decisão 3: sem snapshots); o valor dos bens vem das avaliações até a data.
"""

import uuid
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from src.features.accounts.models import AccountType
from src.features.assets import service as assets_service
from src.features.debts import service as debts_service
from src.features.investments import service as investments_service
from src.features.reports import balances_dre
from src.features.reports.cash_flow import add_months, last_of_month

ZERO = Decimal("0.00")
MAX_MONTHS = 60


def money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"))


@dataclass
class AccountItem:
    account_id: uuid.UUID
    name: str
    amount: Decimal
    is_archived: bool


@dataclass
class AssetItem:
    asset_id: uuid.UUID
    name: str
    kind: str
    value: Decimal
    valued_at: date | None
    is_stale: bool
    debt_outstanding: Decimal | None  # saldo devedor do financiamento vinculado
    equity: Decimal  # valor − saldo devedor (RF-046)


@dataclass
class InvestmentItem:
    asset_id: uuid.UUID
    name: str
    asset_class: str
    market_value: Decimal
    cost: Decimal
    unrealized: Decimal
    price_date: date | None
    has_quote: bool
    is_stale_quote: bool


@dataclass
class DebtItem:
    account_id: uuid.UUID
    name: str
    amount: Decimal
    short_term: Decimal | None  # só para a data de hoje (parcelas em aberto não existem no passado)
    long_term: Decimal | None


@dataclass
class NetWorth:
    as_of: date
    cash: list[AccountItem]
    assets: list[AssetItem]
    investments: list[InvestmentItem]
    cards: list[AccountItem]
    debts: list[DebtItem]
    cash_total: Decimal
    assets_total: Decimal
    investments_total: Decimal
    total_assets: Decimal
    cards_total: Decimal
    debts_total: Decimal
    debts_short_term: Decimal | None
    debts_long_term: Decimal | None
    total_liabilities: Decimal
    net_worth: Decimal
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class HistoryPoint:
    month: str
    as_of: date
    total_assets: Decimal
    total_liabilities: Decimal
    net_worth: Decimal


def net_worth(db: Session, user_id: uuid.UUID, as_of: date | None = None, today: date | None = None) -> NetWorth:
    """RB-028: PL = Σ caixa + Σ bens − Σ cartões − Σ dívidas, na data `as_of` (RB-031)."""
    today = today or date.today()
    as_of = as_of or today
    snapshot = balances_dre.balances(db, user_id, as_of)
    by_account = {row.account_id: row for row in snapshot.accounts}

    cash = [
        AccountItem(r.account_id, r.name, r.balance, r.is_archived)
        for r in snapshot.accounts
        if r.type in (AccountType.CHECKING, AccountType.SAVINGS) and (r.balance != 0 or not r.is_archived)
    ]
    cards = [
        AccountItem(r.account_id, r.name, money(-r.balance), r.is_archived)
        for r in snapshot.accounts
        if r.type == AccountType.CREDIT_CARD and (r.balance != 0 or not r.is_archived)
    ]

    short_by_account = debts_service.short_term_principal(db, user_id, today) if as_of == today else None
    debts: list[DebtItem] = []
    for r in snapshot.accounts:
        if r.type != AccountType.LOAN:
            continue
        outstanding = max(money(-r.balance), ZERO)
        if outstanding == 0:
            continue
        short = None
        long = None
        if short_by_account is not None:
            short = min(short_by_account.get(r.account_id, ZERO), outstanding)
            long = outstanding - short
        debts.append(DebtItem(r.account_id, r.name, outstanding, short, long))

    debt_account = debts_service.debt_account_ids(db, user_id)
    outstanding_by_account = {d.account_id: d.amount for d in debts}
    assets: list[AssetItem] = []
    for view in assets_service.list_views(db, user_id, as_of):
        if view.value == 0:
            continue
        linked = debt_account.get(view.asset.debt_id) if view.asset.debt_id else None
        owed = outstanding_by_account.get(linked, ZERO) if linked else None
        assets.append(
            AssetItem(
                asset_id=view.asset.id,
                name=view.asset.name,
                kind=view.asset.kind,
                value=view.value,
                valued_at=view.valued_at,
                is_stale=view.is_stale,
                debt_outstanding=owed,
                equity=view.value - (owed or ZERO),
            )
        )

    # RB-032: investimentos entram pelo valor de mercado; o saldo da conta `investment` (custo) fica de fora.
    investments = [
        InvestmentItem(
            asset_id=v.asset.id,
            name=v.asset.name,
            asset_class=v.asset.asset_class,
            market_value=v.market_value,
            cost=v.cost,
            unrealized=v.unrealized,
            price_date=v.price_date,
            has_quote=v.has_quote,
            is_stale_quote=v.is_stale_quote,
        )
        for v in investments_service.portfolio(db, user_id, as_of, include_empty=False)
    ]
    investments_total = sum((i.market_value for i in investments), ZERO)
    cash_total = sum((i.amount for i in cash), ZERO)
    assets_total = sum((i.value for i in assets), ZERO)
    cards_total = sum((i.amount for i in cards), ZERO)
    debts_total = sum((i.amount for i in debts), ZERO)
    total_assets = cash_total + assets_total + investments_total
    total_liabilities = cards_total + debts_total

    warnings: list[str] = []
    if any(i.is_stale for i in assets):
        warnings.append("Há bens com avaliação de mais de 12 meses; atualize para o patrimônio não ficar defasado.")
    if any(i.has_quote is False for i in investments):
        warnings.append("Há investimentos sem cotação: aparecem pelo custo até você atualizar ou informar o valor.")
    if any(i.is_stale_quote for i in investments):
        warnings.append("Há investimentos com cotação de mais de 3 dias úteis; atualize para o patrimônio não ficar defasado.")
    if any(by_account[a.account_id].balance < 0 for a in cash):
        warnings.append("Há conta de caixa com saldo negativo: confira o saldo inicial em Contas.")

    return NetWorth(
        as_of=as_of,
        cash=cash,
        assets=assets,
        investments=investments,
        cards=cards,
        debts=debts,
        cash_total=money(cash_total),
        assets_total=money(assets_total),
        investments_total=money(investments_total),
        total_assets=money(total_assets),
        cards_total=money(cards_total),
        debts_total=money(debts_total),
        debts_short_term=money(sum((i.short_term or ZERO for i in debts), ZERO)) if short_by_account is not None else None,
        debts_long_term=money(sum((i.long_term or ZERO for i in debts), ZERO)) if short_by_account is not None else None,
        total_liabilities=money(total_liabilities),
        net_worth=money(total_assets - total_liabilities),
        warnings=warnings,
    )


def history(
    db: Session, user_id: uuid.UUID, months: int = 12, today: date | None = None
) -> list[HistoryPoint]:
    """RF-045: patrimônio no fim de cada mês (o mês corrente termina em hoje)."""
    today = today or date.today()
    current_first = today.replace(day=1)
    points: list[HistoryPoint] = []
    for offset in range(months - 1, -1, -1):
        first = add_months(current_first, -offset)
        as_of = min(last_of_month(first), today)
        worth = net_worth(db, user_id, as_of, today=today)
        points.append(
            HistoryPoint(
                month=f"{first:%Y-%m}",
                as_of=as_of,
                total_assets=worth.total_assets,
                total_liabilities=worth.total_liabilities,
                net_worth=worth.net_worth,
            )
        )
    return points
