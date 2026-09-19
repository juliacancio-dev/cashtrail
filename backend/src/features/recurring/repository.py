import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.features.recurring.models import RecurringFrequency, RecurringTransaction
from src.features.transactions.models import TransactionType


def list_by_user(db: Session, user_id: uuid.UUID) -> list[RecurringTransaction]:
    return list(
        db.scalars(
            select(RecurringTransaction)
            .where(RecurringTransaction.user_id == user_id)
            .order_by(RecurringTransaction.created_at)
        )
    )


def get_by_id_and_user(
    db: Session, recurring_id: uuid.UUID, user_id: uuid.UUID
) -> RecurringTransaction | None:
    """RNF-001: toda leitura já nasce filtrada por user_id, nunca só por id."""
    return db.scalar(
        select(RecurringTransaction).where(
            RecurringTransaction.id == recurring_id, RecurringTransaction.user_id == user_id
        )
    )


def list_due(db: Session, as_of: date) -> list[RecurringTransaction]:
    """Consulta de sistema (job agendado), atravessa todos os usuários de propósito —
    não é uma rota autenticada, não se aplica RNF-001 aqui.
    """
    return list(
        db.scalars(
            select(RecurringTransaction).where(
                RecurringTransaction.is_active.is_(True),
                RecurringTransaction.next_occurrence_date <= as_of,
            )
        )
    )


def create(
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
    recurring = RecurringTransaction(
        user_id=user_id,
        account_id=account_id,
        category_id=category_id,
        type=type,
        amount=amount,
        description=description,
        frequency=frequency,
        next_occurrence_date=next_occurrence_date,
    )
    db.add(recurring)
    db.commit()
    db.refresh(recurring)
    return recurring


def update(
    db: Session,
    recurring: RecurringTransaction,
    amount: Decimal | None,
    description: str | None,
    frequency: RecurringFrequency | None,
) -> RecurringTransaction:
    if amount is not None:
        recurring.amount = amount
    if description is not None:
        recurring.description = description
    if frequency is not None:
        recurring.frequency = frequency
    db.commit()
    db.refresh(recurring)
    return recurring


def deactivate(db: Session, recurring: RecurringTransaction) -> RecurringTransaction:
    recurring.is_active = False
    db.commit()
    db.refresh(recurring)
    return recurring


def advance_next_occurrence(db: Session, recurring: RecurringTransaction, next_date: date) -> None:
    recurring.next_occurrence_date = next_date
    db.commit()
