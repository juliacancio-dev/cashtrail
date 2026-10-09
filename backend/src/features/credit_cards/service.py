import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from src.features.accounts import service as accounts_service
from src.features.accounts.models import AccountType
from src.features.credit_cards import cycle, repository
from src.features.credit_cards.models import CardInvoicePayment, CardPurchase, CreditCard
from src.features.transactions import service as transactions_service
from src.features.transactions.models import Transaction, TransactionType
from src.features.transfers import service as transfers_service

ZERO = Decimal("0.00")
SOON_DAYS = 7
MAX_INSTALLMENTS = 60


class CardNotFoundError(Exception):
    pass


class PaymentNotFoundError(Exception):
    pass


class PurchaseNotFoundError(Exception):
    pass


class InvalidAccountError(Exception):
    pass


class InvalidCategoryError(Exception):
    pass


class ArchivedAccountError(Exception):
    pass


class NotCreditCardAccountError(Exception):
    """RF-024: só uma conta do tipo cartão de crédito pode ter configuração de cartão."""


class CardAlreadyExistsError(Exception):
    pass


class InvalidInvoiceError(Exception):
    """A data informada não é um fechamento válido deste cartão."""


class InvalidAmountError(Exception):
    """RB-018: pagamento acima do saldo da fatura."""


class InvoiceAlreadyPaidError(Exception):
    pass


class AccountRequiredError(Exception):
    """O pagamento precisa de uma conta de origem: a informada ou a padrão do cartão."""


class SameAccountError(Exception):
    pass


class FutureDateError(Exception):
    pass


class InvalidInstallmentsError(Exception):
    pass


@dataclass(frozen=True)
class CardView:
    card: CreditCard
    account_name: str
    debt: Decimal
    available: Decimal | None


@dataclass(frozen=True)
class InvoiceEntry:
    transaction: Transaction
    invoice_closing_date: date
    # True quando a fatura difere da calculada pela data (o usuário moveu a compra, ou parcela futura).
    moved: bool


@dataclass
class Invoice:
    closing_date: date
    period_start: date
    due_date: date
    status: str
    total: Decimal
    paid: Decimal
    balance: Decimal
    # Faturas vizinhas: a tela move uma compra para elas sem refazer a matemática de datas.
    previous_closing_date: date
    next_closing_date: date
    entries: list[InvoiceEntry] = field(default_factory=list)
    payments: list[CardInvoicePayment] = field(default_factory=list)


# ---------- cartão ----------

def _get_card(db: Session, user_id: uuid.UUID, card_id: uuid.UUID) -> CreditCard:
    card = repository.get_card(db, card_id, user_id)
    if card is None:
        raise CardNotFoundError(card_id)
    return card


def _check_usable_account(db: Session, user_id: uuid.UUID, account_id: uuid.UUID):
    try:
        account = accounts_service.get_account(db, user_id, account_id)
    except accounts_service.AccountNotFoundError:
        raise InvalidAccountError(account_id)
    if account.is_archived:
        raise ArchivedAccountError(account_id)
    return account


def _debt(db: Session, user_id: uuid.UUID, card: CreditCard) -> Decimal:
    """Dívida do cartão (RB-020): compras − estornos − pagamentos recebidos + saques/transferências para fora.
    Inclui as parcelas futuras, como o limite de um cartão de verdade."""
    income, expense = transactions_service.totals_by_account(db, user_id, card.account_id)
    incoming = transfers_service.sum_into_account(db, user_id, card.account_id)
    outgoing = transfers_service.sum_out_of_account(db, user_id, card.account_id)
    # quantize: sem lançamentos as somas vêm como Decimal("0") e a API devolveria "0", não "0.00".
    return (expense - income - incoming + outgoing).quantize(Decimal("0.01"))


def _view(db: Session, user_id: uuid.UUID, card: CreditCard) -> CardView:
    debt = _debt(db, user_id, card)
    account = accounts_service.get_account(db, user_id, card.account_id)
    available = card.credit_limit - debt if card.credit_limit is not None else None
    return CardView(card=card, account_name=account.name, debt=debt, available=available)


def create_card(
    db: Session,
    user_id: uuid.UUID,
    account_id: uuid.UUID,
    closing_day: int,
    due_day: int,
    credit_limit: Decimal | None,
    default_payment_account_id: uuid.UUID | None,
) -> CardView:
    account = _check_usable_account(db, user_id, account_id)
    if account.type != AccountType.CREDIT_CARD:
        raise NotCreditCardAccountError(account_id)
    if repository.get_card_by_account(db, account_id, user_id) is not None:
        raise CardAlreadyExistsError(account_id)
    if default_payment_account_id is not None:
        if default_payment_account_id == account_id:
            raise SameAccountError(account_id)
        _check_usable_account(db, user_id, default_payment_account_id)

    card = CreditCard(
        user_id=user_id,
        account_id=account_id,
        closing_day=closing_day,
        due_day=due_day,
        credit_limit=credit_limit,
        default_payment_account_id=default_payment_account_id,
    )
    repository.add(db, card)
    db.commit()
    db.refresh(card)
    return _view(db, user_id, card)


def list_cards(db: Session, user_id: uuid.UUID) -> list[CardView]:
    return [_view(db, user_id, card) for card in repository.list_cards(db, user_id)]


def get_card(db: Session, user_id: uuid.UUID, card_id: uuid.UUID) -> CardView:
    return _view(db, user_id, _get_card(db, user_id, card_id))


def _remap_closing_dates(db: Session, user_id: uuid.UUID, card: CreditCard, new_closing_day: int) -> None:
    """Mudar o dia de fechamento mantém cada fatura no MESMO mês: as faturas escolhidas
    (compras movidas) e os pagamentos acompanham o novo dia, em vez de ficarem órfãos."""
    for link_tx_id in list(repository.links_by_card(db, card.id)):
        link = repository.get_link(db, link_tx_id)
        link.invoice_closing_date = cycle.closing_date_in_month(
            link.invoice_closing_date.year, link.invoice_closing_date.month, new_closing_day
        )
    for payment in repository.list_payments(db, card.id, user_id):
        payment.invoice_closing_date = cycle.closing_date_in_month(
            payment.invoice_closing_date.year, payment.invoice_closing_date.month, new_closing_day
        )


def update_card(db: Session, user_id: uuid.UUID, card_id: uuid.UUID, changes: dict[str, Any]) -> CardView:
    card = _get_card(db, user_id, card_id)

    if "default_payment_account_id" in changes and changes["default_payment_account_id"] is not None:
        if changes["default_payment_account_id"] == card.account_id:
            raise SameAccountError(card.account_id)
        _check_usable_account(db, user_id, changes["default_payment_account_id"])

    if "closing_day" in changes and changes["closing_day"] != card.closing_day:
        _remap_closing_dates(db, user_id, card, changes["closing_day"])

    for name in ("closing_day", "due_day", "credit_limit", "default_payment_account_id"):
        if name in changes:
            setattr(card, name, changes[name])

    db.commit()
    db.refresh(card)
    return _view(db, user_id, card)


# ---------- faturas ----------

def _signed(transaction: Transaction) -> Decimal:
    """Compra soma, estorno (receita na conta do cartão) subtrai (RB-017)."""
    return transaction.amount if transaction.type == TransactionType.EXPENSE else -transaction.amount


def _make_invoice(
    card: CreditCard,
    closing_date: date,
    entries: list[InvoiceEntry],
    payments: list[CardInvoicePayment],
    today: date,
) -> Invoice:
    start = cycle.period_start(closing_date, card.closing_day)
    due = cycle.due_date_for(closing_date, card.due_day)
    total = sum((_signed(e.transaction) for e in entries), ZERO)
    paid = sum((p.amount for p in payments), ZERO)
    balance = total - paid
    return Invoice(
        closing_date=closing_date,
        period_start=start,
        due_date=due,
        status=cycle.invoice_status(closing_date, due, start, balance, today),
        total=total,
        paid=paid,
        balance=balance,
        previous_closing_date=cycle.shift_closing(closing_date, -1, card.closing_day),
        next_closing_date=cycle.shift_closing(closing_date, 1, card.closing_day),
        entries=entries,
        payments=payments,
    )


def _build_invoices(db: Session, user_id: uuid.UUID, card: CreditCard, today: date) -> dict[date, Invoice]:
    links = repository.links_by_card(db, card.id)
    entries: dict[date, list[InvoiceEntry]] = defaultdict(list)
    for transaction in transactions_service.list_by_account(db, user_id, card.account_id):
        derived = cycle.invoice_closing_for(transaction.occurred_at, card.closing_day)
        linked = links.get(transaction.id)
        closing = linked or derived
        entries[closing].append(InvoiceEntry(transaction, closing, moved=linked is not None and linked != derived))

    payments: dict[date, list[CardInvoicePayment]] = defaultdict(list)
    for payment in repository.list_payments(db, card.id, user_id):
        payments[payment.invoice_closing_date].append(payment)

    current = cycle.invoice_closing_for(today, card.closing_day)
    closings = set(entries) | set(payments) | {current}
    return {c: _make_invoice(card, c, entries.get(c, []), payments.get(c, []), today) for c in closings}


def list_invoices(
    db: Session, user_id: uuid.UUID, card_id: uuid.UUID, today: date | None = None, limit: int = 36
) -> list[Invoice]:
    today = today or date.today()
    card = _get_card(db, user_id, card_id)
    invoices = sorted(_build_invoices(db, user_id, card, today).values(), key=lambda i: i.closing_date, reverse=True)
    return invoices[:limit]


def get_invoice(
    db: Session, user_id: uuid.UUID, card_id: uuid.UUID, closing_date: date, today: date | None = None
) -> Invoice:
    today = today or date.today()
    card = _get_card(db, user_id, card_id)
    if not cycle.is_valid_closing_date(closing_date, card.closing_day):
        raise InvalidInvoiceError(closing_date)
    invoices = _build_invoices(db, user_id, card, today)
    return invoices.get(closing_date) or _make_invoice(card, closing_date, [], [], today)


# ---------- compras ----------

def create_purchase(
    db: Session,
    user_id: uuid.UUID,
    card_id: uuid.UUID,
    description: str,
    amount: Decimal,
    purchase_date: date,
    category_id: uuid.UUID,
    installments: int = 1,
    invoice_closing_date: date | None = None,
) -> list[InvoiceEntry]:
    """RF-025/RF-026. Cada parcela é uma despesa normal na conta do cartão (decisão 4), datada
    em um mês diferente e ligada à fatura do seu ciclo; o `amount` é o TOTAL."""
    if not 1 <= installments <= MAX_INSTALLMENTS:
        raise InvalidInstallmentsError(installments)

    card = _get_card(db, user_id, card_id)
    first_closing = invoice_closing_date or cycle.invoice_closing_for(purchase_date, card.closing_day)
    if not cycle.is_valid_closing_date(first_closing, card.closing_day):
        raise InvalidInvoiceError(first_closing)

    parts = cycle.split_amount(amount, installments)
    drafts = [
        transactions_service.TransactionDraft(
            category_id=category_id,
            type=TransactionType.EXPENSE,
            amount=part,
            description=(f"{description} ({index + 1}/{installments})" if installments > 1 else description)[:255],
            occurred_at=cycle.add_months(purchase_date, index),
        )
        for index, part in enumerate(parts)
    ]

    try:
        created = transactions_service.create_many(
            db, user_id, card.account_id, drafts, source=transactions_service.TransactionSource.MANUAL, commit=False
        )
    except transactions_service.InvalidAccountError:
        raise InvalidAccountError(card.account_id)
    except transactions_service.ArchivedAccountError:
        raise ArchivedAccountError(card.account_id)
    except transactions_service.InvalidCategoryError:
        raise InvalidCategoryError(category_id)

    db.flush()  # atribui os ids dos lançamentos para ligar cada um à sua fatura
    entries = []
    for index, transaction in enumerate(created):
        closing = cycle.shift_closing(first_closing, index, card.closing_day)
        repository.add(db, CardPurchase(transaction_id=transaction.id, credit_card_id=card.id, invoice_closing_date=closing))
        derived = cycle.invoice_closing_for(transaction.occurred_at, card.closing_day)
        entries.append(InvoiceEntry(transaction, closing, moved=closing != derived))

    db.commit()
    return entries


def move_purchase(
    db: Session, user_id: uuid.UUID, card_id: uuid.UUID, transaction_id: uuid.UUID, invoice_closing_date: date
) -> InvoiceEntry:
    """Muda a fatura de uma compra (como no Mobills). Vale também para lançamentos antigos da conta do cartão."""
    card = _get_card(db, user_id, card_id)
    if not cycle.is_valid_closing_date(invoice_closing_date, card.closing_day):
        raise InvalidInvoiceError(invoice_closing_date)

    try:
        transaction = transactions_service.get_transaction(db, user_id, transaction_id)
    except transactions_service.TransactionNotFoundError:
        raise PurchaseNotFoundError(transaction_id)
    if transaction.account_id != card.account_id:
        raise PurchaseNotFoundError(transaction_id)

    link = repository.get_link(db, transaction.id)
    if link is None:
        repository.add(
            db, CardPurchase(transaction_id=transaction.id, credit_card_id=card.id, invoice_closing_date=invoice_closing_date)
        )
    else:
        link.invoice_closing_date = invoice_closing_date

    db.commit()
    derived = cycle.invoice_closing_for(transaction.occurred_at, card.closing_day)
    return InvoiceEntry(transaction, invoice_closing_date, moved=invoice_closing_date != derived)


# ---------- pagamento da fatura ----------

def pay_invoice(
    db: Session,
    user_id: uuid.UUID,
    card_id: uuid.UUID,
    closing_date: date,
    amount: Decimal | None,
    paid_at: date | None,
    from_account_id: uuid.UUID | None,
    today: date | None = None,
) -> CardInvoicePayment:
    """RF-028: o pagamento é uma TRANSFERÊNCIA da conta de origem para a conta do cartão (RB-014):
    quita a dívida sem criar despesa nova, então o dashboard não muda."""
    today = today or date.today()
    card = _get_card(db, user_id, card_id)
    invoice = get_invoice(db, user_id, card_id, closing_date, today)

    if invoice.balance <= 0:
        raise InvoiceAlreadyPaidError(closing_date)

    amount = invoice.balance if amount is None else amount
    if amount <= 0 or amount > invoice.balance:
        raise InvalidAmountError(closing_date)  # RB-018

    paid_at = paid_at or today
    if paid_at > today:
        raise FutureDateError(paid_at)

    source_account_id = from_account_id or card.default_payment_account_id
    if source_account_id is None:
        raise AccountRequiredError(card_id)

    card_account = accounts_service.get_account(db, user_id, card.account_id)
    try:
        transfer = transfers_service.create_transfer(
            db,
            user_id,
            from_account_id=source_account_id,
            to_account_id=card.account_id,
            amount=amount,
            occurred_at=paid_at,
            description=f"Fatura {card_account.name} {closing_date.strftime('%m/%Y')}",
            commit=False,
            today=today,
        )
    except transfers_service.InvalidAccountError:
        raise InvalidAccountError(source_account_id)
    except transfers_service.ArchivedAccountError:
        raise ArchivedAccountError(source_account_id)
    except transfers_service.SameAccountError:
        raise SameAccountError(source_account_id)
    except transfers_service.FutureDateError:
        raise FutureDateError(paid_at)

    payment = CardInvoicePayment(
        user_id=user_id,
        credit_card_id=card.id,
        invoice_closing_date=closing_date,
        transfer_id=transfer.id,
        amount=amount,
        paid_at=paid_at,
    )
    repository.add(db, payment)
    db.commit()
    db.refresh(payment)
    return payment


def undo_payment(
    db: Session, user_id: uuid.UUID, card_id: uuid.UUID, closing_date: date, payment_id: uuid.UUID
) -> None:
    """Desfaz o pagamento apagando o vínculo E a transferência que ele criou."""
    card = _get_card(db, user_id, card_id)
    payment = repository.get_payment(db, payment_id, card.id, user_id)
    if payment is None or payment.invoice_closing_date != closing_date:
        raise PaymentNotFoundError(payment_id)

    transfer_id = payment.transfer_id
    repository.delete(db, payment)
    transfers_service.delete_transfer(db, user_id, transfer_id, commit=False)
    db.commit()


# ---------- resumo para o alerta (RF-030) ----------

def summary(db: Session, user_id: uuid.UUID, today: date | None = None, days: int = SOON_DAYS) -> dict[str, Any]:
    """Faturas vencidas e a vencer. Só conta faturas já fechadas: o valor das abertas ainda muda."""
    today = today or date.today()
    limit = today + timedelta(days=days)
    result: dict[str, Any] = {
        "days": days,
        "overdue_count": 0,
        "overdue_amount": ZERO,
        "due_soon_count": 0,
        "due_soon_amount": ZERO,
        "debt": ZERO,
    }
    for card in repository.list_cards(db, user_id):
        result["debt"] += _debt(db, user_id, card)
        for invoice in _build_invoices(db, user_id, card, today).values():
            if invoice.closing_date >= today or invoice.balance <= 0:
                continue
            if invoice.due_date < today:
                result["overdue_count"] += 1
                result["overdue_amount"] += invoice.balance
            elif invoice.due_date <= limit:
                result["due_soon_count"] += 1
                result["due_soon_amount"] += invoice.balance
    return result
