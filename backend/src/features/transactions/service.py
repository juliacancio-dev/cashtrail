import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from src.features.accounts import service as accounts_service
from src.features.categories import service as categories_service
from src.features.transactions import repository
from src.features.transactions.models import Transaction, TransactionType


class TransactionNotFoundError(Exception):
    pass


class InvalidAccountError(Exception):
    pass


class InvalidCategoryError(Exception):
    pass


class ArchivedAccountError(Exception):
    """RB-003 (10-data-model.md): conta arquivada não aceita novos lançamentos."""

    pass


def list_transactions(
    db: Session, user_id: uuid.UUID, start_date: date | None = None, end_date: date | None = None
) -> list[Transaction]:
    return repository.list_by_user(db, user_id, start_date, end_date)


def get_transaction(db: Session, user_id: uuid.UUID, transaction_id: uuid.UUID) -> Transaction:
    transaction = repository.get_by_id_and_user(db, transaction_id, user_id)
    if transaction is None:
        raise TransactionNotFoundError(transaction_id)

    return transaction


def create_transaction(
    db: Session,
    user_id: uuid.UUID,
    account_id: uuid.UUID,
    category_id: uuid.UUID,
    type: TransactionType,
    amount: Decimal,
    description: str | None,
    occurred_at: date,
) -> Transaction:
    """RB-001: lançamento pertence a exatamente uma conta e uma categoria do próprio usuário."""
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
        occurred_at=occurred_at,
    )
