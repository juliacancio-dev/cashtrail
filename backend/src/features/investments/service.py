import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.features.accounts import service as accounts_service
from src.features.accounts.models import NON_CASH_TYPES, AccountType
from src.features.categories import service as categories_service
from src.features.investments import position as position_math
from src.features.investments import repository
from src.features.investments.models import (
    ASSET_CLASSES,
    QUOTE_SOURCES,
    InvestmentAsset,
    InvestmentOperation,
    InvestmentQuote,
    QuoteRequestLog,
)
from src.features.investments.providers import IndexError_, IndexProvider, QuoteError, QuoteProvider
from src.features.transactions import service as transactions_service
from src.features.transactions.models import TransactionType
from src.features.transfers import service as transfers_service

ZERO = Decimal("0.00")
STALE_QUOTE_DAYS = 5  # ~3 dias úteis (R-13.5)


class AssetNotFoundError(Exception):
    pass


class OperationNotFoundError(Exception):
    pass


class InvalidAccountError(Exception):
    """Conta inexistente, de outro usuário, ou do tipo errado para o uso."""


class ArchivedAccountError(Exception):
    pass


class InvalidCategoryError(Exception):
    pass


class CategoryRequiredError(Exception):
    """Provento e venda com ganho/perda geram lançamento financeiro: precisam de categoria."""


class InvalidClassError(Exception):
    pass


class DuplicateSymbolError(Exception):
    pass


class InvalidOperationError(Exception):
    pass


class PositionInvalidError(Exception):
    """Venda acima da quantidade em carteira, ou ajuste que a deixaria negativa."""


class ChronologyError(Exception):
    """Operação anterior à última do ativo: mudaria retroativamente o custo médio das vendas."""


class NotLastOperationError(Exception):
    """Só a última operação do ativo pode ser desfeita (as seguintes dependem dela)."""


class FutureDateError(Exception):
    pass


@dataclass(frozen=True)
class PositionView:
    asset: InvestmentAsset
    quantity: Decimal
    avg_cost: Decimal
    cost: Decimal
    price: Decimal | None
    price_date: date | None
    price_source: str | None
    market_value: Decimal  # sem cotação, usa o custo (e has_quote = False)
    has_quote: bool
    is_stale_quote: bool
    unrealized: Decimal
    unrealized_pct: Decimal | None
    invested: Decimal
    proceeds: Decimal
    income: Decimal
    realized: Decimal
    total_return: Decimal
    total_return_pct: Decimal | None
    first_buy: date | None


@dataclass(frozen=True)
class RefreshResult:
    updated: list[str]
    failed: list[str]
    skipped_for_cap: list[str]
    requests_this_month: int
    monthly_cap: int


@dataclass(frozen=True)
class Benchmark:
    since: date | None
    invested: Decimal
    portfolio_return_pct: Decimal | None
    cdi_return_pct: Decimal | None
    difference_pct: Decimal | None
    note: str


def _money(value: Decimal) -> Decimal:
    return position_math.money(value)


def _pct(numerator: Decimal, denominator: Decimal) -> Decimal | None:
    if denominator <= 0:
        return None
    return (numerator / denominator * 100).quantize(Decimal("0.01"))


# ---------- ativos ----------

def _investment_account(db: Session, user_id: uuid.UUID, account_id: uuid.UUID):
    try:
        account = accounts_service.get_account(db, user_id, account_id)
    except accounts_service.AccountNotFoundError:
        raise InvalidAccountError(account_id)
    if account.type != AccountType.INVESTMENT:
        raise InvalidAccountError(account_id)
    if account.is_archived:
        raise ArchivedAccountError(account_id)
    return account


def _cash_account(db: Session, user_id: uuid.UUID, account_id: uuid.UUID):
    try:
        account = accounts_service.get_account(db, user_id, account_id)
    except accounts_service.AccountNotFoundError:
        raise InvalidAccountError(account_id)
    if account.type in NON_CASH_TYPES:
        raise InvalidAccountError(account_id)
    if account.is_archived:
        raise ArchivedAccountError(account_id)
    return account


def _get_asset(db: Session, user_id: uuid.UUID, asset_id: uuid.UUID) -> InvestmentAsset:
    asset = repository.get_asset(db, asset_id, user_id)
    if asset is None:
        raise AssetNotFoundError(asset_id)
    return asset


def create_asset(
    db: Session,
    user_id: uuid.UUID,
    account_id: uuid.UUID,
    name: str,
    symbol: str | None,
    asset_class: str,
    quote_source: str,
) -> InvestmentAsset:
    if asset_class not in ASSET_CLASSES or quote_source not in QUOTE_SOURCES:
        raise InvalidClassError(asset_class)
    _investment_account(db, user_id, account_id)
    symbol = symbol.strip().upper() if symbol and symbol.strip() else None
    if quote_source == "brapi" and symbol is None:
        raise InvalidClassError("cotacao automatica exige o simbolo")

    asset = InvestmentAsset(
        user_id=user_id,
        account_id=account_id,
        name=name,
        symbol=symbol,
        asset_class=asset_class,
        quote_source=quote_source,
    )
    try:
        repository.add(db, asset)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise DuplicateSymbolError(symbol)
    return asset


def update_asset(db: Session, user_id: uuid.UUID, asset_id: uuid.UUID, changes: dict) -> InvestmentAsset:
    asset = _get_asset(db, user_id, asset_id)
    if "quote_source" in changes and changes["quote_source"] not in QUOTE_SOURCES:
        raise InvalidClassError(changes["quote_source"])
    for field in ("name", "symbol", "quote_source", "is_archived"):
        if field in changes:
            value = changes[field]
            if field == "symbol" and value:
                value = value.strip().upper()
            setattr(asset, field, value or None if field == "symbol" else value)
    if asset.quote_source == "brapi" and not asset.symbol:
        db.rollback()
        raise InvalidClassError("cotacao automatica exige o simbolo")
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise DuplicateSymbolError(asset.symbol)
    return asset


# ---------- posição e carteira ----------

def _ops_for(rows: list[InvestmentOperation], on: date | None = None) -> list[position_math.Op]:
    return [
        position_math.Op(r.kind, r.occurred_at, r.quantity, r.unit_price, r.fees, r.amount)
        for r in rows
        if on is None or r.occurred_at <= on
    ]


def _view(
    asset: InvestmentAsset,
    rows: list[InvestmentOperation],
    quotes: list[InvestmentQuote],
    on: date,
) -> PositionView:
    position = position_math.replay(_ops_for(rows, on))
    candidates = [q for q in quotes if q.quoted_on <= on]
    latest = max(candidates, key=lambda q: q.quoted_on) if candidates else None

    has_quote = latest is not None and position.quantity > 0
    if has_quote:
        market = _money(position.quantity * latest.price)
    else:
        market = _money(position.cost)
    unrealized = market - _money(position.cost)
    returned = position.proceeds + position.income
    total_return = market + returned - position.invested
    stale = bool(has_quote and (on - latest.quoted_on).days > STALE_QUOTE_DAYS)

    return PositionView(
        asset=asset,
        quantity=position.quantity,
        avg_cost=position.avg_cost,
        cost=_money(position.cost),
        price=latest.price if latest else None,
        price_date=latest.quoted_on if latest else None,
        price_source=latest.source if latest else None,
        market_value=market,
        has_quote=bool(has_quote),
        is_stale_quote=stale,
        unrealized=unrealized,
        unrealized_pct=_pct(unrealized, position.cost) if position.quantity > 0 else None,
        invested=_money(position.invested),
        proceeds=_money(position.proceeds),
        income=_money(position.income),
        realized=_money(position.realized),
        total_return=_money(total_return),
        total_return_pct=_pct(total_return, position.invested),
        first_buy=position.first_buy,
    )


def portfolio(db: Session, user_id: uuid.UUID, on: date | None = None, include_empty: bool = True) -> list[PositionView]:
    """RF-053. `on` permite a carteira em datas passadas (patrimônio histórico): usa as operações e
    a última cotação guardada até a data (RB-032)."""
    on = on or date.today()
    ops_by_asset: dict[uuid.UUID, list[InvestmentOperation]] = {}
    for op in repository.list_operations(db, user_id):
        ops_by_asset.setdefault(op.asset_id, []).append(op)
    quotes_by_asset: dict[uuid.UUID, list[InvestmentQuote]] = {}
    for quote in repository.list_quotes(db, user_id):
        quotes_by_asset.setdefault(quote.asset_id, []).append(quote)

    views = []
    for asset in repository.list_assets(db, user_id):
        view = _view(asset, ops_by_asset.get(asset.id, []), quotes_by_asset.get(asset.id, []), on)
        if include_empty or view.quantity > 0:
            views.append(view)
    return views


def get_detail(
    db: Session, user_id: uuid.UUID, asset_id: uuid.UUID, on: date | None = None
) -> tuple[PositionView, list[InvestmentOperation]]:
    on = on or date.today()
    asset = _get_asset(db, user_id, asset_id)
    rows = repository.list_operations(db, user_id, asset.id)
    quotes = repository.list_quotes(db, user_id, asset.id)
    return _view(asset, rows, quotes, on), rows


# ---------- operações ----------

def _record_trade_quote(db: Session, user_id: uuid.UUID, asset: InvestmentAsset, day: date, price: Decimal) -> None:
    """Dá um primeiro ponto de preço ao histórico quando ainda não há cotação do dia."""
    if price > 0 and repository.get_quote_on(db, asset.id, day, user_id) is None:
        repository.add(
            db, InvestmentQuote(user_id=user_id, asset_id=asset.id, quoted_on=day, price=price, source="trade")
        )


def add_operation(
    db: Session,
    user_id: uuid.UUID,
    asset_id: uuid.UUID,
    kind: str,
    occurred_at: date,
    quantity: Decimal,
    unit_price: Decimal,
    fees: Decimal,
    amount: Decimal,
    cash_account_id: uuid.UUID | None,
    category_id: uuid.UUID | None,
    note: str | None,
    today: date | None = None,
) -> InvestmentOperation:
    """RF-050 a RF-052. Cria a operação e o que ela move (transferência e/ou lançamento) na MESMA transação."""
    today = today or date.today()
    asset = _get_asset(db, user_id, asset_id)
    if kind not in ("buy", "sell", "income", "adjust"):
        raise InvalidOperationError(kind)
    if occurred_at > today:
        raise FutureDateError(occurred_at)

    existing = repository.list_operations(db, user_id, asset.id)
    if existing and occurred_at < existing[-1].occurred_at:
        raise ChronologyError(occurred_at)

    investment_account = _investment_account(db, user_id, asset.account_id)
    position = position_math.replay(_ops_for(existing))

    if kind in ("buy", "sell"):
        if quantity <= 0 or unit_price <= 0 or fees < 0:
            raise InvalidOperationError(kind)
    if kind == "income" and amount <= 0:
        raise InvalidOperationError(kind)
    if kind == "adjust" and quantity == 0:
        raise InvalidOperationError(kind)

    cost_basis = gain = None
    op_amount = ZERO
    if kind == "buy":
        op_amount = position_math.buy_cost(quantity, unit_price, fees)
    elif kind == "sell":
        op_amount = position_math.sell_proceeds(quantity, unit_price, fees)
    elif kind == "income":
        op_amount = _money(amount)

    new_op = position_math.Op(kind, occurred_at, quantity, unit_price, fees, op_amount)
    try:
        cost_basis, gain = position_math.apply(position, new_op)
    except position_math.PositionError:
        raise PositionInvalidError(kind)

    cash = None
    if kind != "adjust":
        if cash_account_id is None:
            raise InvalidAccountError(None)
        cash = _cash_account(db, user_id, cash_account_id)

    needs_category = kind == "income" or (kind == "sell" and gain not in (None, ZERO))
    if needs_category:
        if category_id is None:
            raise CategoryRequiredError(kind)
        try:
            categories_service.get_category(db, user_id, category_id)
        except categories_service.CategoryNotFoundError:
            raise InvalidCategoryError(category_id)

    transfer = transaction = None
    label = asset.symbol or asset.name
    try:
        if kind == "buy":
            transfer = transfers_service.create_transfer(
                db, user_id, from_account_id=cash.id, to_account_id=investment_account.id,
                amount=op_amount, occurred_at=occurred_at, description=f"Compra {label}"[:255],
                commit=False, today=today,
            )
        elif kind == "sell":
            if cost_basis and cost_basis > 0:
                transfer = transfers_service.create_transfer(
                    db, user_id, from_account_id=investment_account.id, to_account_id=cash.id,
                    amount=cost_basis, occurred_at=occurred_at, description=f"Venda {label}"[:255],
                    commit=False, today=today,
                )
            if gain and gain != 0:
                transaction = transactions_service.create_transaction(
                    db, user_id, account_id=cash.id, category_id=category_id,
                    type=TransactionType.INCOME if gain > 0 else TransactionType.EXPENSE,
                    amount=abs(gain),
                    description=f"{'Ganho' if gain > 0 else 'Perda'} na venda de {label}"[:255],
                    occurred_at=occurred_at, commit=False,
                )
        elif kind == "income":
            transaction = transactions_service.create_transaction(
                db, user_id, account_id=cash.id, category_id=category_id, type=TransactionType.INCOME,
                amount=op_amount, description=f"Provento {label}"[:255], occurred_at=occurred_at, commit=False,
            )
    except (transfers_service.InvalidAccountError, transactions_service.InvalidAccountError):
        raise InvalidAccountError(cash_account_id)
    except (transfers_service.ArchivedAccountError, transactions_service.ArchivedAccountError):
        raise ArchivedAccountError(cash_account_id)
    except transactions_service.InvalidCategoryError:
        raise InvalidCategoryError(category_id)

    operation = InvestmentOperation(
        user_id=user_id,
        asset_id=asset.id,
        kind=kind,
        occurred_at=occurred_at,
        quantity=quantity,
        unit_price=unit_price,
        fees=fees,
        amount=op_amount,
        cost_basis=cost_basis,
        gain=gain,
        cash_account_id=cash.id if cash else None,
        category_id=category_id if needs_category else None,
        transfer_id=transfer.id if transfer else None,
        transaction_id=transaction.id if transaction else None,
        note=note,
    )
    repository.add(db, operation)
    if kind in ("buy", "sell"):
        _record_trade_quote(db, user_id, asset, occurred_at, unit_price)
    db.commit()
    db.refresh(operation)
    return operation


def undo_operation(
    db: Session, user_id: uuid.UUID, asset_id: uuid.UUID, operation_id: uuid.UUID
) -> None:
    """Só a última operação do ativo: as seguintes dependem do custo médio que ela deixou."""
    asset = _get_asset(db, user_id, asset_id)
    operation = repository.get_operation(db, operation_id, asset.id, user_id)
    if operation is None:
        raise OperationNotFoundError(operation_id)
    rows = repository.list_operations(db, user_id, asset.id)
    if rows[-1].id != operation.id:
        raise NotLastOperationError(operation_id)

    transfer_id, transaction_id = operation.transfer_id, operation.transaction_id
    repository.delete(db, operation)
    if transaction_id is not None:
        transactions_service.delete_transaction(db, user_id, transaction_id, commit=False)
    if transfer_id is not None:
        transfers_service.delete_transfer(db, user_id, transfer_id, commit=False)
    db.commit()


# ---------- cotações ----------

def set_manual_quote(
    db: Session,
    user_id: uuid.UUID,
    asset_id: uuid.UUID,
    price: Decimal,
    quoted_on: date | None,
    today: date | None = None,
) -> InvestmentQuote:
    """RF-056: valor informado à mão (renda fixa, fundo, outro) ou correção de uma cotação."""
    today = today or date.today()
    asset = _get_asset(db, user_id, asset_id)
    quoted_on = quoted_on or today
    if quoted_on > today:
        raise FutureDateError(quoted_on)
    if price < 0:
        raise InvalidOperationError("price")

    quote = repository.get_quote_on(db, asset.id, quoted_on, user_id)
    if quote is None:
        quote = InvestmentQuote(user_id=user_id, asset_id=asset.id, quoted_on=quoted_on, price=price, source="manual")
        repository.add(db, quote)
    else:
        quote.price = price
        quote.source = "manual"
    db.commit()
    return quote


def _month_start(now: datetime) -> datetime:
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def refresh_quotes(
    db: Session,
    user_id: uuid.UUID,
    provider: QuoteProvider,
    today: date | None = None,
    monthly_cap: int = 10000,
    now: datetime | None = None,
) -> RefreshResult:
    """RF-055: uma requisição por ativo com cotação automática; para no teto mensal; falha de um
    ativo não impede os outros nem apaga a última cotação conhecida (RF-054)."""
    today = today or date.today()
    now = now or datetime.now(timezone.utc)
    used = repository.count_requests_since(db, _month_start(now))

    updated: list[str] = []
    failed: list[str] = []
    skipped: list[str] = []
    for asset in repository.list_assets(db, user_id):
        if asset.is_archived or asset.quote_source != "brapi" or not asset.symbol:
            continue
        if used >= monthly_cap:
            skipped.append(asset.symbol)
            continue
        used += 1
        try:
            price = provider.get_price(asset.symbol)
        except QuoteError:
            repository.add(db, QuoteRequestLog(provider=provider.name, symbol=asset.symbol, ok=False))
            failed.append(asset.symbol)
            continue
        repository.add(db, QuoteRequestLog(provider=provider.name, symbol=asset.symbol, ok=True))
        quote = repository.get_quote_on(db, asset.id, today, user_id)
        if quote is None:
            repository.add(
                db, InvestmentQuote(user_id=user_id, asset_id=asset.id, quoted_on=today, price=price, source="brapi")
            )
        else:
            quote.price = price
            quote.source = "brapi"
        updated.append(asset.symbol)
    db.commit()
    return RefreshResult(updated, failed, skipped, used, monthly_cap)


def refresh_all_users(
    db: Session, provider: QuoteProvider, today: date | None = None, monthly_cap: int = 10000
) -> int:
    """Job diário: atualiza a carteira de todos os usuários que têm ativo com cotação automática."""
    total = 0
    for user_id in repository.users_with_auto_assets(db):
        total += len(refresh_quotes(db, user_id, provider, today, monthly_cap).updated)
    return total


def requests_this_month(db: Session, now: datetime | None = None) -> int:
    return repository.count_requests_since(db, _month_start(now or datetime.now(timezone.utc)))


# ---------- comparativo ----------

def benchmark(
    db: Session, user_id: uuid.UUID, index_provider: IndexProvider, today: date | None = None
) -> Benchmark:
    """RF-057/decisão 4: retorno simples da carteira × CDI acumulado desde a primeira compra."""
    today = today or date.today()
    views = portfolio(db, user_id, today)
    invested = sum((v.invested for v in views), ZERO)
    first_buys = [v.first_buy for v in views if v.first_buy is not None]
    note = (
        "Retorno simples sobre o total aportado; com aportes em datas muito diferentes ele é "
        "impreciso (não é rentabilidade ponderada pelo tempo)."
    )
    if invested <= 0 or not first_buys:
        return Benchmark(None, invested, None, None, None, note)

    since = min(first_buys)
    value = sum((v.market_value for v in views), ZERO)
    returned = sum((v.proceeds + v.income for v in views), ZERO)
    portfolio_pct = _pct(value + returned - invested, invested)

    cdi_pct: Decimal | None = None
    try:
        factor = Decimal(1)
        for _, daily in index_provider.cdi_daily(since, today):
            factor *= Decimal(1) + daily / Decimal(100)
        cdi_pct = ((factor - 1) * 100).quantize(Decimal("0.01"))
    except IndexError_:
        note += " O CDI não pôde ser consultado agora."

    difference = portfolio_pct - cdi_pct if portfolio_pct is not None and cdi_pct is not None else None
    return Benchmark(since, invested, portfolio_pct, cdi_pct, difference, note)
