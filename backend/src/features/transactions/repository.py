import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.features.transactions.models import Transaction, TransactionSource, TransactionType


def list_by_user(
    db: Session,
    user_id: uuid.UUID,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[Transaction]:
    stmt = select(Transaction).where(Transaction.user_id == user_id)
    if start_date is not None:
        stmt = stmt.where(Transaction.occurred_at >= start_date)
    if end_date is not None:
        stmt = stmt.where(Transaction.occurred_at <= end_date)

    return list(db.scalars(stmt.order_by(Transaction.occurred_at, Transaction.created_at)))


def get_by_id_and_user(db: Session, transaction_id: uuid.UUID, user_id: uuid.UUID) -> Transaction | None:
    """RNF-001: toda leitura já nasce filtrada por user_id, nunca só por id."""
    return db.scalar(
        select(Transaction).where(Transaction.id == transaction_id, Transaction.user_id == user_id)
    )


def create(
    db: Session,
    user_id: uuid.UUID,
    account_id: uuid.UUID,
    category_id: uuid.UUID,
    type: TransactionType,
    amount: Decimal,
    description: str | None,
    occurred_at: date,
    goal_id: uuid.UUID | None = None,
    source: TransactionSource = TransactionSource.MANUAL,
    recurring_transaction_id: uuid.UUID | None = None,
) -> Transaction:
    transaction = Transaction(
        user_id=user_id,
        account_id=account_id,
        category_id=category_id,
        goal_id=goal_id,
        recurring_transaction_id=recurring_transaction_id,
        type=type,
        source=source,
        amount=amount,
        description=description,
        occurred_at=occurred_at,
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


def sum_by_goal(db: Session, user_id: uuid.UUID, goal_id: uuid.UUID) -> Decimal:
    total = db.scalar(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == user_id, Transaction.goal_id == goal_id
        )
    )
    return Decimal(total)


def sum_by_category_period(
    db: Session, user_id: uuid.UUID, category_id: uuid.UUID, start_date: date, end_date: date
) -> Decimal:
    total = db.scalar(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == user_id,
            Transaction.category_id == category_id,
            Transaction.type == TransactionType.EXPENSE,
            Transaction.occurred_at >= start_date,
            Transaction.occurred_at <= end_date,
        )
    )
    return Decimal(total)
