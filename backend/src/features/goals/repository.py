import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.features.goals.models import Goal


def list_by_user(db: Session, user_id: uuid.UUID) -> list[Goal]:
    return list(db.scalars(select(Goal).where(Goal.user_id == user_id).order_by(Goal.created_at)))


def get_by_id_and_user(db: Session, goal_id: uuid.UUID, user_id: uuid.UUID) -> Goal | None:
    """RNF-001: toda leitura já nasce filtrada por user_id, nunca só por id."""
    return db.scalar(select(Goal).where(Goal.id == goal_id, Goal.user_id == user_id))


def create(
    db: Session, user_id: uuid.UUID, name: str, target_amount: Decimal, target_date: date | None
) -> Goal:
    goal = Goal(user_id=user_id, name=name, target_amount=target_amount, target_date=target_date)
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


def update(
    db: Session,
    goal: Goal,
    name: str | None,
    target_amount: Decimal | None,
    target_date: date | None,
    clear_target_date: bool,
) -> Goal:
    if name is not None:
        goal.name = name
    if target_amount is not None:
        goal.target_amount = target_amount
    if clear_target_date:
        goal.target_date = None
    elif target_date is not None:
        goal.target_date = target_date
    db.commit()
    db.refresh(goal)
    return goal


def mark_achieved(db: Session, goal: Goal, achieved: bool) -> Goal:
    goal.is_achieved = achieved
    db.commit()
    db.refresh(goal)
    return goal


def delete(db: Session, goal: Goal) -> None:
    db.delete(goal)
    db.commit()
