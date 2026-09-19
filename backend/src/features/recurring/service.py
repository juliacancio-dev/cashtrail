import calendar
import uuid
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from src.features.accounts import service as accounts_service
from src.features.categories import service as categories_service
from src.features.recurring import repository
from src.features.recurring.models import RecurringFrequency, RecurringTransaction
from src.features.transactions import service as transactions_service
from src.features.transactions.models import TransactionSource, TransactionType


class RecurringNotFoundError(Exception):
    pass


class InvalidAccountError(Exception):
    pass


class InvalidCategoryError(Exception):
    pass


class ArchivedAccountError(Exception):
    pass


def _advance(current: date, frequency: RecurringFrequency) -> date:
    if frequency == RecurringFrequency.WEEKLY:
        return current + timedelta(days=7)

    # monthly: avança um mês, corrigindo dias que não existem no mês seguinte (ex: 31 -> 28/29/30)
    month = current.month + 1
    year = current.year + (month - 1) // 12
    month = (month - 1) % 12 + 1
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(current.day, last_day))


def list_recurring(db: Session, user_id: uuid.UUID) -> list[RecurringTransaction]:
    return repository.list_by_user(db, user_id)


def get_recurring(db: Session, user_id: uuid.UUID, recurring_id: uuid.UUID) -> RecurringTransaction:
    recurring = repository.get_by_id_and_user(db, recurring_id, user_id)
    if recurring is None:
        raise RecurringNotFoundError(recurring_id)

    return recurring


def create_recurring(
    db: Session,
    user_id: uuid.UUID,
    account_id: uuid.UUID,
    category_id: uuid.UUID,
    type: TransactionType,
    amount: Decimal,
    description: str | None,
    frequency: RecurringFrequency,
    next_occurrence_date: date,
) -> RecurringTransaction:
    """Mesma validação de posse/estado de conta que transactions.create_transaction (RB-001)."""
    try:
        account = accounts_service.get_account(db, user_id, account_id)
    except accounts_service.AccountNotFoundError:
        raise InvalidAccountError(account_id)

    if account.is_archived:
        raise ArchivedAccountError(account_id)

    try:
        categories_service.get_category(db, user_id, category_id)
    except categories_service.CategoryNotFoundError:
        raise InvalidCategoryError(category_id)

    return repository.create(
        db,
        user_id=user_id,
        account_id=account_id,
        category_id=category_id,
        type=type,
        amount=amount,
        description=description,
        frequency=frequency,
        next_occurrence_date=next_occurrence_date,
    )


def update_recurring(
    db: Session,
    user_id: uuid.UUID,
    recurring_id: uuid.UUID,
    amount: Decimal | None,
    description: str | None,
    frequency: RecurringFrequency | None,
) -> RecurringTransaction:
    recurring = get_recurring(db, user_id, recurring_id)
    return repository.update(db, recurring, amount, description, frequency)


def deactivate_recurring(db: Session, user_id: uuid.UUID, recurring_id: uuid.UUID) -> RecurringTransaction:
    """RB-004: só um cancelamento explícito interrompe a geração futura."""
    recurring = get_recurring(db, user_id, recurring_id)
    return repository.deactivate(db, recurring)


def generate_due_transactions(db: Session, as_of: date | None = None) -> int:
    """Job agendado (ADR-005/APScheduler): para toda recorrência ativa vencida,
    gera o lançamento via transactions.service (nunca insere direto na tabela,
    09-vertical-slices.md) e avança a próxima ocorrência. Roda para todos os
    usuários — não é uma requisição autenticada.
    """
    as_of = as_of or date.today()
    due = repository.list_due(db, as_of)

    generated = 0
    for recurring in due:
        try:
            transactions_service.create_transaction(
                db,
                recurring.user_id,
                account_id=recurring.account_id,
                category_id=recurring.category_id,
                type=recurring.type,
                amount=recurring.amount,
                description=recurring.description,
                occurred_at=recurring.next_occurrence_date,
                source=TransactionSource.RECURRING,
                recurring_transaction_id=recurring.id,
            )
        except (
            transactions_service.InvalidAccountError,
            transactions_service.InvalidCategoryError,
            transactions_service.ArchivedAccountError,
        ):
            # conta/categoria ficou inválida depois que a recorrência foi criada —
            # não avança a data, tenta de novo na próxima execução do job.
            continue

        repository.advance_next_occurrence(db, recurring, _advance(recurring.next_occurrence_date, recurring.frequency))
        generated += 1

    return generated
