import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from src.features.goals import repository
from src.features.goals.models import Goal
from src.features.transactions import service as transactions_service
from src.features.transactions.models import Transaction, TransactionType


class GoalNotFoundError(Exception):
    pass


def list_goals(db: Session, user_id: uuid.UUID) -> list[Goal]:
    return repository.list_by_user(db, user_id)


def get_goal(db: Session, user_id: uuid.UUID, goal_id: uuid.UUID) -> Goal:
    goal = repository.get_by_id_and_user(db, goal_id, user_id)
    if goal is None:
        raise GoalNotFoundError(goal_id)

    return goal


def get_progress(db: Session, user_id: uuid.UUID, goal_id: uuid.UUID) -> Decimal:
    """RB-003: progresso = soma dos lançamentos vinculados à meta."""
    return transactions_service.sum_by_goal(db, user_id, goal_id)


def create_goal(
    db: Session, user_id: uuid.UUID, name: str, target_amount: Decimal, target_date: date | None
) -> Goal:
    return repository.create(db, user_id=user_id, name=name, target_amount=target_amount, target_date=target_date)


def update_goal(
    db: Session,
    user_id: uuid.UUID,
    goal_id: uuid.UUID,
    name: str | None,
    target_amount: Decimal | None,
    target_date: date | None,
    clear_target_date: bool = False,
) -> Goal:
    goal = get_goal(db, user_id, goal_id)
    return repository.update(db, goal, name, target_amount, target_date, clear_target_date)


def delete_goal(db: Session, user_id: uuid.UUID, goal_id: uuid.UUID) -> None:
    goal = get_goal(db, user_id, goal_id)
    repository.delete(db, goal)


def create_contribution(
    db: Session,
    user_id: uuid.UUID,
    goal_id: uuid.UUID,
    account_id: uuid.UUID,
    category_id: uuid.UUID,
    type: TransactionType,
    amount: Decimal,
    description: str | None,
    occurred_at: date,
) -> Transaction:
    """Cria um lançamento já vinculado à meta e recalcula se ela foi atingida (evento MetaAtingida).

    goals depende de transactions (nunca o contrário, 09-vertical-slices.md), então
    é aqui — e não em transactions.service — que a posse da meta é validada.
    """
    goal = get_goal(db, user_id, goal_id)

    transaction = transactions_service.create_transaction(
        db,
        user_id,
        account_id=account_id,
        category_id=category_id,
        type=type,
        amount=amount,
        description=description,
        occurred_at=occurred_at,
        goal_id=goal_id,
    )

    progress = get_progress(db, user_id, goal_id)
    if progress >= goal.target_amount and not goal.is_achieved:
        repository.mark_achieved(db, goal, True)

    return transaction
