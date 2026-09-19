import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.features.budgets.models import Budget


def list_by_user(db: Session, user_id: uuid.UUID, month: date | None = None) -> list[Budget]:
    stmt = select(Budget).where(Budget.user_id == user_id)
    if month is not None:
        stmt = stmt.where(Budget.month == month)

    return list(db.scalars(stmt.order_by(Budget.month)))


def get_by_id_and_user(db: Session, budget_id: uuid.UUID, user_id: uuid.UUID) -> Budget | None:
    """RNF-001: toda leitura já nasce filtrada por user_id, nunca só por id."""
    return db.scalar(select(Budget).where(Budget.id == budget_id, Budget.user_id == user_id))


def get_by_category_and_month(
    db: Session, user_id: uuid.UUID, category_id: uuid.UUID, month: date
) -> Budget | None:
    """RB-002: no máximo um orçamento por categoria+mês, por usuário."""
    return db.scalar(
        select(Budget).where(
            Budget.user_id == user_id, Budget.category_id == category_id, Budget.month == month
        )
    )


def create(db: Session, user_id: uuid.UUID, category_id: uuid.UUID, month: date, limit_amount: Decimal) -> Budget:
    budget = Budget(user_id=user_id, category_id=category_id, month=month, limit_amount=limit_amount)
    db.add(budget)
    db.commit()
    db.refresh(budget)
    return budget


def update_limit(db: Session, budget: Budget, limit_amount: Decimal) -> Budget:
    budget.limit_amount = limit_amount
    db.commit()
    db.refresh(budget)
    return budget


def delete(db: Session, budget: Budget) -> None:
    db.delete(budget)
    db.commit()
