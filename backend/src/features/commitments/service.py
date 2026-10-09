import calendar
import uuid
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from src.features.accounts import service as accounts_service
from src.features.categories import service as categories_service
from src.features.commitments import repository
from src.features.commitments.models import Commitment, CommitmentDirection, CommitmentSettlement
from src.features.transactions import service as transactions_service
from src.features.transactions.models import TransactionType

SOON_DAYS = 7
MAX_INSTALLMENTS = 120
ZERO = Decimal("0.00")

STATUSES = ("open", "due_today", "overdue", "partially_paid", "paid", "canceled")


class CommitmentNotFoundError(Exception):
    pass


class SettlementNotFoundError(Exception):
    pass


class InvalidAccountError(Exception):
    pass


class InvalidCategoryError(Exception):
    pass


class ArchivedAccountError(Exception):
    """RB-010: conta arquivada não aceita novos lançamentos (reaproveita RB-003)."""


class CommitmentLockedError(Exception):
    """RB-013: cancelado ou totalmente pago não pode ser alterado/cancelado/baixado de novo."""


class InvalidAmountError(Exception):
    """RB-011: baixa acima do saldo, ou valor menor do que já foi pago."""


class AccountRequiredError(Exception):
    """A baixa precisa de uma conta: a prevista no compromisso ou uma informada na hora."""


class FutureDateError(Exception):
    """Pagamento no futuro criaria lançamento realizado 'fantasma'."""


class InvalidInstallmentsError(Exception):
    pass


@dataclass(frozen=True)
class CommitmentView:
    commitment: Commitment
    paid_amount: Decimal
    balance: Decimal
    status: str


def add_months(base: date, months: int) -> date:
    """Soma meses preservando o dia, com ajuste para meses mais curtos (31 -> 28/29/30)."""
    month_index = base.month - 1 + months
    year = base.year + month_index // 12
    month = month_index % 12 + 1
    return date(year, month, min(base.day, calendar.monthrange(year, month)[1]))


def split_amount(total: Decimal, count: int) -> list[Decimal]:
    """RB-012: a soma das parcelas é sempre o total; os centavos que sobram vão na primeira."""
    cents = int((total * 100).to_integral_value())
    base, remainder = divmod(cents, count)
    values = [base] * count
    values[0] += remainder
    return [(Decimal(value) / 100).quantize(Decimal("0.01")) for value in values]


def derive_status(commitment: Commitment, paid: Decimal, today: date) -> str:
    """RB-009: 'atrasado' é derivado, nunca gravado."""
    if commitment.is_canceled:
        return "canceled"
    if commitment.amount - paid <= 0:
        return "paid"
    if commitment.due_date < today:
        return "overdue"
    if commitment.due_date == today:
        return "due_today"
    if paid > 0:
        return "partially_paid"
    return "open"


def _view(commitment: Commitment, paid: Decimal, today: date) -> CommitmentView:
    return CommitmentView(
        commitment=commitment,
        paid_amount=paid,
        balance=commitment.amount - paid,
        status=derive_status(commitment, paid, today),
    )


def _validate_refs(
    db: Session, user_id: uuid.UUID, category_id: uuid.UUID | None, account_id: uuid.UUID | None
) -> None:
    if category_id is not None:
        try:
            categories_service.get_category(db, user_id, category_id)
        except categories_service.CategoryNotFoundError:
            raise InvalidCategoryError(category_id)

    if account_id is not None:
        try:
            account = accounts_service.get_account(db, user_id, account_id)
        except accounts_service.AccountNotFoundError:
            raise InvalidAccountError(account_id)
        if account.is_archived:
            raise ArchivedAccountError(account_id)


def _get(db: Session, user_id: uuid.UUID, commitment_id: uuid.UUID) -> Commitment:
    commitment = repository.get_by_id_and_user(db, commitment_id, user_id)
    if commitment is None:
        raise CommitmentNotFoundError(commitment_id)
    return commitment


def create_commitment(
    db: Session,
    user_id: uuid.UUID,
    direction: CommitmentDirection,
    description: str,
    counterparty: str | None,
    amount: Decimal,
    due_date: date,
    category_id: uuid.UUID,
    account_id: uuid.UUID | None,
    notes: str | None,
    installments: int = 1,
    today: date | None = None,
    recurring_transaction_id: uuid.UUID | None = None,
) -> list[CommitmentView]:
    """RF-014/RF-015. O `amount` é o TOTAL; com N > 1 vira N compromissos mensais.

    `recurring_transaction_id` só é passado pela slice recurring (RF-022); a posse da
    recorrência já foi garantida por quem chama, como acontece com `goal_id` em transactions.
    """
    if not 1 <= installments <= MAX_INSTALLMENTS:
        raise InvalidInstallmentsError(installments)
    _validate_refs(db, user_id, category_id, account_id)

    today = today or date.today()
    group_id = uuid.uuid4() if installments > 1 else None
    rows = [
        Commitment(
            user_id=user_id,
            direction=direction,
            description=description,
            counterparty=counterparty,
            amount=part,
            due_date=add_months(due_date, index),
            category_id=category_id,
            account_id=account_id,
            notes=notes,
            recurring_transaction_id=recurring_transaction_id,
            installment_group_id=group_id,
            installment_number=index + 1 if group_id else None,
            installment_count=installments if group_id else None,
            is_canceled=False,
        )
        for index, part in enumerate(split_amount(amount, installments))
    ]
    repository.add_all(db, rows)
    return [_view(row, ZERO, today) for row in rows]


def has_commitment_for_recurrence(
    db: Session, user_id: uuid.UUID, recurring_id: uuid.UUID, due_date: date
) -> bool:
    """Idempotência do job de recorrência: já existe o compromisso desta ocorrência?"""
    return repository.exists_for_recurrence(db, user_id, recurring_id, due_date)


def list_commitments(
    db: Session,
    user_id: uuid.UUID,
    direction: CommitmentDirection | None = None,
    status: str | None = None,
    due_from: date | None = None,
    due_to: date | None = None,
    category_id: uuid.UUID | None = None,
    account_id: uuid.UUID | None = None,
    today: date | None = None,
) -> tuple[list[CommitmentView], dict[str, Any]]:
    """RF-019. `status` aceita qualquer situação derivada e também 'pending' (tudo que tem saldo)."""
    today = today or date.today()
    rows = repository.list_with_paid(db, user_id, direction, due_from, due_to, category_id, account_id)
    views = [_view(commitment, paid, today) for commitment, paid in rows]

    if status == "pending":
        views = [v for v in views if v.status not in ("paid", "canceled")]
    elif status is not None:
        views = [v for v in views if v.status == status]

    live = [v for v in views if v.status not in ("paid", "canceled")]
    totals = {
        "count": len(views),
        "payable_balance": sum(
            (v.balance for v in live if v.commitment.direction == CommitmentDirection.PAYABLE), ZERO
        ),
        "receivable_balance": sum(
            (v.balance for v in live if v.commitment.direction == CommitmentDirection.RECEIVABLE), ZERO
        ),
    }
    return views, totals


def get_commitment(
    db: Session, user_id: uuid.UUID, commitment_id: uuid.UUID, today: date | None = None
) -> tuple[CommitmentView, list[CommitmentSettlement]]:
    today = today or date.today()
    commitment = _get(db, user_id, commitment_id)
    paid = repository.paid_amount(db, commitment.id)
    return _view(commitment, paid, today), repository.list_settlements(db, commitment.id, user_id)


def update_commitment(
    db: Session,
    user_id: uuid.UUID,
    commitment_id: uuid.UUID,
    changes: dict[str, Any],
    today: date | None = None,
) -> CommitmentView:
    today = today or date.today()
    commitment = _get(db, user_id, commitment_id)
    paid = repository.paid_amount(db, commitment.id)
    status = derive_status(commitment, paid, today)

    if ("amount" in changes or "due_date" in changes) and status in ("paid", "canceled"):
        raise CommitmentLockedError(commitment_id)
    if "amount" in changes and changes["amount"] < paid:
        raise InvalidAmountError(commitment_id)

    _validate_refs(db, user_id, changes.get("category_id"), changes.get("account_id"))
    for field in ("description", "counterparty", "notes", "category_id", "account_id", "amount", "due_date"):
        if field in changes:
            setattr(commitment, field, changes[field])

    repository.save(db, commitment)
    return _view(commitment, paid, today)


def cancel_commitment(
    db: Session, user_id: uuid.UUID, commitment_id: uuid.UUID, today: date | None = None
) -> CommitmentView:
    """RF-020. Cancela só o que ainda está em aberto; o que já foi pago fica no histórico."""
    today = today or date.today()
    commitment = _get(db, user_id, commitment_id)
    paid = repository.paid_amount(db, commitment.id)
    if derive_status(commitment, paid, today) in ("paid", "canceled"):
        raise CommitmentLockedError(commitment_id)

    commitment.is_canceled = True
    repository.save(db, commitment)
    return _view(commitment, paid, today)


def settle_commitment(
    db: Session,
    user_id: uuid.UUID,
    commitment_id: uuid.UUID,
    amount: Decimal | None,
    paid_at: date | None,
    account_id: uuid.UUID | None,
    today: date | None = None,
) -> tuple[CommitmentView, CommitmentSettlement]:
    """RF-016/RF-017: cria o lançamento realizado e a baixa na MESMA transação.

    O lançamento nasce via transactions.service (nunca direto na tabela), que revalida
    posse de conta/categoria (RB-001) e conta arquivada (RB-010).
    """
    today = today or date.today()
    commitment = _get(db, user_id, commitment_id)
    paid = repository.paid_amount(db, commitment.id)
    balance = commitment.amount - paid

    if commitment.is_canceled or balance <= 0:
        raise CommitmentLockedError(commitment_id)

    amount = balance if amount is None else amount
    if amount <= 0 or amount > balance:
        raise InvalidAmountError(commitment_id)  # RB-011

    paid_at = paid_at or today
    if paid_at > today:
        raise FutureDateError(paid_at)

    target_account_id = account_id or commitment.account_id
    if target_account_id is None:
        raise AccountRequiredError(commitment_id)

    description = commitment.description
    if commitment.installment_number and commitment.installment_count:
        description = f"{description} ({commitment.installment_number}/{commitment.installment_count})"

    try:
        transaction = transactions_service.create_transaction(
            db,
            user_id,
            account_id=target_account_id,
            category_id=commitment.category_id,
            type=TransactionType.EXPENSE if commitment.direction == CommitmentDirection.PAYABLE else TransactionType.INCOME,
            amount=amount,
            description=description[:255],
            occurred_at=paid_at,
            commit=False,
        )
    except transactions_service.InvalidAccountError:
        raise InvalidAccountError(target_account_id)
    except transactions_service.ArchivedAccountError:
        raise ArchivedAccountError(target_account_id)
    except transactions_service.InvalidCategoryError:
        raise InvalidCategoryError(commitment.category_id)

    settlement = CommitmentSettlement(
        user_id=user_id,
        commitment_id=commitment.id,
        transaction_id=transaction.id,
        amount=amount,
        paid_at=paid_at,
    )
    repository.add_settlement(db, settlement)
    db.commit()
    db.refresh(settlement)
    return _view(commitment, paid + amount, today), settlement


def undo_settlement(
    db: Session,
    user_id: uuid.UUID,
    commitment_id: uuid.UUID,
    settlement_id: uuid.UUID,
    today: date | None = None,
) -> CommitmentView:
    """Decisão 8: desfaz uma baixa apagando a baixa E o lançamento que ela criou.

    Só mexe em lançamentos que esta slice criou (os ligados a uma baixa); a API de
    lançamentos continua sem DELETE.
    """
    today = today or date.today()
    commitment = _get(db, user_id, commitment_id)
    settlement = repository.get_settlement(db, settlement_id, commitment.id, user_id)
    if settlement is None:
        raise SettlementNotFoundError(settlement_id)

    transaction_id = settlement.transaction_id
    repository.delete_settlement(db, settlement)
    transactions_service.delete_transaction(db, user_id, transaction_id, commit=False)
    db.commit()

    return _view(commitment, repository.paid_amount(db, commitment.id), today)


def summary(db: Session, user_id: uuid.UUID, today: date | None = None, days: int = SOON_DAYS) -> dict[str, Any]:
    """RF-021: vencidos e próximos vencimentos, para o alerta do dashboard."""
    today = today or date.today()
    limit = today + timedelta(days=days)
    result: dict[str, Any] = {"days": days}
    for direction in CommitmentDirection:
        result[direction.value] = {
            "overdue_count": 0,
            "overdue_amount": ZERO,
            "due_soon_count": 0,
            "due_soon_amount": ZERO,
            "open_amount": ZERO,
        }

    for commitment, paid in repository.list_with_paid(db, user_id):
        view = _view(commitment, paid, today)
        if view.status in ("paid", "canceled"):
            continue
        bucket = result[commitment.direction.value]
        bucket["open_amount"] += view.balance
        if commitment.due_date < today:
            bucket["overdue_count"] += 1
            bucket["overdue_amount"] += view.balance
        elif commitment.due_date <= limit:
            bucket["due_soon_count"] += 1
            bucket["due_soon_amount"] += view.balance
    return result
