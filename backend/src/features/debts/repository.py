import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.features.debts.models import Debt, DebtAmortization, DebtInstallment


def list_debts(db: Session, user_id: uuid.UUID) -> list[Debt]:
    return list(db.scalars(select(Debt).where(Debt.user_id == user_id).order_by(Debt.created_at)))


def get_debt(db: Session, debt_id: uuid.UUID, user_id: uuid.UUID) -> Debt | None:
    """RNF-001: toda leitura já nasce filtrada por user_id, nunca só por id."""
    return db.scalar(select(Debt).where(Debt.id == debt_id, Debt.user_id == user_id))


def list_installments(db: Session, debt_id: uuid.UUID, user_id: uuid.UUID) -> list[DebtInstallment]:
    return list(
        db.scalars(
            select(DebtInstallment)
            .where(DebtInstallment.debt_id == debt_id, DebtInstallment.user_id == user_id)
            .order_by(DebtInstallment.number, DebtInstallment.created_at)
        )
    )


def get_installment(
    db: Session, installment_id: uuid.UUID, debt_id: uuid.UUID, user_id: uuid.UUID
) -> DebtInstallment | None:
    return db.scalar(
        select(DebtInstallment).where(
            DebtInstallment.id == installment_id,
            DebtInstallment.debt_id == debt_id,
            DebtInstallment.user_id == user_id,
        )
    )


def list_amortizations(db: Session, debt_id: uuid.UUID, user_id: uuid.UUID) -> list[DebtAmortization]:
    return list(
        db.scalars(
            select(DebtAmortization)
            .where(DebtAmortization.debt_id == debt_id, DebtAmortization.user_id == user_id)
            .order_by(DebtAmortization.paid_at, DebtAmortization.created_at)
        )
    )


def add(db: Session, *rows: object) -> None:
    """Só adiciona e dá flush: o commit é do service, junto com o que as outras slices criaram."""
    db.add_all(rows)
    db.flush()
