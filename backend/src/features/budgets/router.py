import uuid
from datetime import date
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.dependencies import CurrentUser
from src.features.budgets import service
from src.features.budgets.models import Budget
from src.features.budgets.schemas import BudgetCreate, BudgetRead, BudgetUpdate
from src.features.categories import service as categories_service

router = APIRouter(prefix="/budgets", tags=["budgets"])


def _parse_month(value: str) -> date:
    year, month = value.split("-")
    return date(int(year), int(month), 1)


def _to_read(db: Session, user_id: uuid.UUID, budget: Budget) -> BudgetRead:
    category = categories_service.get_category(db, user_id, budget.category_id)
    spent_amount = service.get_spent_amount(db, user_id, budget)
    percent_consumed = (
        (spent_amount / budget.limit_amount * 100) if budget.limit_amount > 0 else Decimal("0")
    )
    return BudgetRead(
        id=budget.id,
        category_id=budget.category_id,
        category_name=category.name,
        month=budget.month.strftime("%Y-%m"),
        limit_amount=budget.limit_amount,
        spent_amount=spent_amount,
        percent_consumed=percent_consumed.quantize(Decimal("0.01")),
        is_exceeded=spent_amount > budget.limit_amount,
    )


@router.get("", response_model=list[BudgetRead])
def list_budgets(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    month: str | None = Query(default=None, pattern=r"^\d{4}-(0[1-9]|1[0-2])$"),
) -> list[BudgetRead]:
    budgets = service.list_budgets(db, current_user.id, _parse_month(month) if month else None)
    return [_to_read(db, current_user.id, b) for b in budgets]


@router.post("", response_model=BudgetRead, status_code=status.HTTP_201_CREATED)
def create_budget(
    payload: BudgetCreate, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> BudgetRead:
    try:
        budget = service.create_budget(
            db, current_user.id, payload.category_id, _parse_month(payload.month), payload.limit_amount
        )
    except service.InvalidCategoryError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="categoria nao encontrada")
    except service.DuplicateBudgetError:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="ja existe orcamento para essa categoria e mes")

    return _to_read(db, current_user.id, budget)


@router.get("/{budget_id}", response_model=BudgetRead)
def get_budget(
    budget_id: uuid.UUID, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> BudgetRead:
    try:
        budget = service.get_budget(db, current_user.id, budget_id)
    except service.BudgetNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="orcamento nao encontrado")

    return _to_read(db, current_user.id, budget)


@router.patch("/{budget_id}", response_model=BudgetRead)
def update_budget(
    budget_id: uuid.UUID,
    payload: BudgetUpdate,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> BudgetRead:
    try:
        budget = service.update_budget_limit(db, current_user.id, budget_id, payload.limit_amount)
    except service.BudgetNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="orcamento nao encontrado")

    return _to_read(db, current_user.id, budget)


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(
    budget_id: uuid.UUID, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> None:
    try:
        service.delete_budget(db, current_user.id, budget_id)
    except service.BudgetNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="orcamento nao encontrado")
