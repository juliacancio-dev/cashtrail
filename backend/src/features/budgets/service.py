import calendar
import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from src.features.budgets import repository
from src.features.budgets.models import Budget
from src.features.categories import service as categories_service
from src.features.transactions import service as transactions_service


class BudgetNotFoundError(Exception):
    pass


class InvalidCategoryError(Exception):
    pass


class DuplicateBudgetError(Exception):
    """RB-002: não pode existir mais de um orçamento para o mesmo par categoria+mês, por usuário."""

    pass


def month_range(month: date) -> tuple[date, date]:
    last_day = calendar.monthrange(month.year, month.month)[1]
    return month.replace(day=1), month.replace(day=last_day)


def list_budgets(db: Session, user_id: uuid.UUID, month: date | None = None) -> list[Budget]:
    return repository.list_by_user(db, user_id, month)


def get_budget(db: Session, user_id: uuid.UUID, budget_id: uuid.UUID) -> Budget:
    budget = repository.get_by_id_and_user(db, budget_id, user_id)
    if budget is None:
        raise BudgetNotFoundError(budget_id)

    return budget


def get_spent_amount(db: Session, user_id: uuid.UUID, budget: Budget) -> Decimal:
    start_date, end_date = month_range(budget.month)
    return transactions_service.sum_by_category_period(db, user_id, budget.category_id, start_date, end_date)


def create_budget(
    db: Session, user_id: uuid.UUID, category_id: uuid.UUID, month: date, limit_amount: Decimal
) -> Budget:
    """RB-002: unicidade por (usuário, categoria, mês)."""
    try:
        categories_service.get_category(db, user_id, category_id)
    except categories_service.CategoryNotFoundError:
        raise InvalidCategoryError(category_id)

    month = month.replace(day=1)
    if repository.get_by_category_and_month(db, user_id, category_id, month) is not None:
        raise DuplicateBudgetError((category_id, month))

    return repository.create(db, user_id=user_id, category_id=category_id, month=month, limit_amount=limit_amount)


def update_budget_limit(db: Session, user_id: uuid.UUID, budget_id: uuid.UUID, limit_amount: Decimal) -> Budget:
    budget = get_budget(db, user_id, budget_id)
    return repository.update_limit(db, budget, limit_amount)


def delete_budget(db: Session, user_id: uuid.UUID, budget_id: uuid.UUID) -> None:
    budget = get_budget(db, user_id, budget_id)
    repository.delete(db, budget)
