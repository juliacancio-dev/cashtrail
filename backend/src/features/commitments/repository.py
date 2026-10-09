import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.features.commitments.models import Commitment, CommitmentDirection, CommitmentSettlement


def _paid_subquery():
    return (
        select(
            CommitmentSettlement.commitment_id.label("commitment_id"),
            func.coalesce(func.sum(CommitmentSettlement.amount), 0).label("paid"),
        )
        .group_by(CommitmentSettlement.commitment_id)
        .subquery()
    )


def list_with_paid(
    db: Session,
    user_id: uuid.UUID,
    direction: CommitmentDirection | None = None,
    due_from: date | None = None,
    due_to: date | None = None,
    category_id: uuid.UUID | None = None,
    account_id: uuid.UUID | None = None,
) -> list[tuple[Commitment, Decimal]]:
    """Compromissos do usuário já com o total pago (soma das baixas) de cada um."""
    paid = _paid_subquery()
    stmt = (
        select(Commitment, func.coalesce(paid.c.paid, 0))
        .outerjoin(paid, paid.c.commitment_id == Commitment.id)
        .where(Commitment.user_id == user_id)
    )
    if direction is not None:
        stmt = stmt.where(Commitment.direction == direction)
    if due_from is not None:
        stmt = stmt.where(Commitment.due_date >= due_from)
    if due_to is not None:
        stmt = stmt.where(Commitment.due_date <= due_to)
    if category_id is not None:
        stmt = stmt.where(Commitment.category_id == category_id)
    if account_id is not None:
        stmt = stmt.where(Commitment.account_id == account_id)

    rows = db.execute(stmt.order_by(Commitment.due_date, Commitment.created_at, Commitment.installment_number))
    return [(commitment, Decimal(total)) for commitment, total in rows]


def get_by_id_and_user(db: Session, commitment_id: uuid.UUID, user_id: uuid.UUID) -> Commitment | None:
    """RNF-001: toda leitura já nasce filtrada por user_id, nunca só por id."""
    return db.scalar(select(Commitment).where(Commitment.id == commitment_id, Commitment.user_id == user_id))


def exists_for_recurrence(db: Session, user_id: uuid.UUID, recurring_id: uuid.UUID, due_date: date) -> bool:
    count = db.scalar(
        select(func.count())
        .select_from(Commitment)
        .where(
            Commitment.user_id == user_id,
            Commitment.recurring_transaction_id == recurring_id,
            Commitment.due_date == due_date,
        )
    )
    return bool(count)


def paid_amount(db: Session, commitment_id: uuid.UUID) -> Decimal:
    total = db.scalar(
        select(func.coalesce(func.sum(CommitmentSettlement.amount), 0)).where(
            CommitmentSettlement.commitment_id == commitment_id
        )
    )
    return Decimal(total)


def list_settlements(db: Session, commitment_id: uuid.UUID, user_id: uuid.UUID) -> list[CommitmentSettlement]:
    return list(
        db.scalars(
            select(CommitmentSettlement)
            .where(CommitmentSettlement.commitment_id == commitment_id, CommitmentSettlement.user_id == user_id)
            .order_by(CommitmentSettlement.paid_at, CommitmentSettlement.created_at)
        )
    )


def get_settlement(
    db: Session, settlement_id: uuid.UUID, commitment_id: uuid.UUID, user_id: uuid.UUID
) -> CommitmentSettlement | None:
    return db.scalar(
        select(CommitmentSettlement).where(
            CommitmentSettlement.id == settlement_id,
            CommitmentSettlement.commitment_id == commitment_id,
            CommitmentSettlement.user_id == user_id,
        )
    )


def add_all(db: Session, commitments: list[Commitment], commit: bool = True) -> None:
    db.add_all(commitments)
    if commit:
        db.commit()
        for commitment in commitments:
            db.refresh(commitment)
    else:
        db.flush()


def add_settlement(db: Session, settlement: CommitmentSettlement) -> None:
    """Só adiciona à sessão: o commit é do service, junto com o lançamento criado."""
    db.add(settlement)
    db.flush()


def delete_settlement(db: Session, settlement: CommitmentSettlement) -> None:
    # flush imediato: a baixa precisa sumir ANTES do lançamento (FK RESTRICT em transaction_id).
    db.delete(settlement)
    db.flush()


def save(db: Session, commitment: Commitment) -> Commitment:
    db.commit()
    db.refresh(commitment)
    return commitment
