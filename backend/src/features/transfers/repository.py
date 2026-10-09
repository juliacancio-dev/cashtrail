import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from src.features.transfers.models import Transfer


def list_by_user(
    db: Session,
    user_id: uuid.UUID,
    start_date: date | None = None,
    end_date: date | None = None,
    account_id: uuid.UUID | None = None,
) -> list[Transfer]:
    stmt = select(Transfer).where(Transfer.user_id == user_id)
    if start_date is not None:
        stmt = stmt.where(Transfer.occurred_at >= start_date)
    if end_date is not None:
        stmt = stmt.where(Transfer.occurred_at <= end_date)
    if account_id is not None:
        stmt = stmt.where(or_(Transfer.from_account_id == account_id, Transfer.to_account_id == account_id))

    return list(db.scalars(stmt.order_by(Transfer.occurred_at, Transfer.created_at)))


def get_by_id_and_user(db: Session, transfer_id: uuid.UUID, user_id: uuid.UUID) -> Transfer | None:
    """RNF-001: toda leitura já nasce filtrada por user_id, nunca só por id."""
    return db.scalar(select(Transfer).where(Transfer.id == transfer_id, Transfer.user_id == user_id))


def create(
    db: Session,
    user_id: uuid.UUID,
    from_account_id: uuid.UUID,
    to_account_id: uuid.UUID,
    amount: Decimal,
    occurred_at: date,
    description: str | None,
    commit: bool = True,
) -> Transfer:
    transfer = Transfer(
        user_id=user_id,
        from_account_id=from_account_id,
        to_account_id=to_account_id,
        amount=amount,
        occurred_at=occurred_at,
        description=description,
    )
    db.add(transfer)
    if commit:
        db.commit()
        db.refresh(transfer)
    else:
        # flush atribui o id sem encerrar a transação do chamador.
        db.flush()
    return transfer


def delete(db: Session, transfer: Transfer, commit: bool = True) -> None:
    db.delete(transfer)
    if commit:
        db.commit()
    else:
        db.flush()


def sum_into_account(db: Session, user_id: uuid.UUID, account_id: uuid.UUID) -> Decimal:
    total = db.scalar(
        select(func.coalesce(func.sum(Transfer.amount), 0)).where(
            Transfer.user_id == user_id, Transfer.to_account_id == account_id
        )
    )
    return Decimal(total)


def sum_out_of_account(db: Session, user_id: uuid.UUID, account_id: uuid.UUID) -> Decimal:
    total = db.scalar(
        select(func.coalesce(func.sum(Transfer.amount), 0)).where(
            Transfer.user_id == user_id, Transfer.from_account_id == account_id
        )
    )
    return Decimal(total)
