import uuid
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.dependencies import CurrentUser
from src.features.goals import service
from src.features.goals.models import Goal
from src.features.goals.schemas import ContributionCreate, GoalCreate, GoalRead, GoalUpdate
from src.features.transactions import service as transactions_service
from src.features.transactions.schemas import TransactionRead

router = APIRouter(prefix="/goals", tags=["goals"])


def _to_read(db: Session, user_id: uuid.UUID, goal: Goal) -> GoalRead:
    current_amount = service.get_progress(db, user_id, goal.id)
    percent_achieved = (
        (current_amount / goal.target_amount * 100) if goal.target_amount > 0 else Decimal("0")
    )
    return GoalRead(
        id=goal.id,
        name=goal.name,
        target_amount=goal.target_amount,
        target_date=goal.target_date,
        is_achieved=goal.is_achieved,
        current_amount=current_amount,
        percent_achieved=percent_achieved.quantize(Decimal("0.01")),
        created_at=goal.created_at,
    )


@router.get("", response_model=list[GoalRead])
def list_goals(current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]) -> list[GoalRead]:
    goals = service.list_goals(db, current_user.id)
    return [_to_read(db, current_user.id, g) for g in goals]


@router.post("", response_model=GoalRead, status_code=status.HTTP_201_CREATED)
def create_goal(
    payload: GoalCreate, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> GoalRead:
    goal = service.create_goal(db, current_user.id, payload.name, payload.target_amount, payload.target_date)
    return _to_read(db, current_user.id, goal)


@router.get("/{goal_id}", response_model=GoalRead)
def get_goal(
    goal_id: uuid.UUID, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> GoalRead:
    try:
        goal = service.get_goal(db, current_user.id, goal_id)
    except service.GoalNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="meta nao encontrada")

    return _to_read(db, current_user.id, goal)


@router.patch("/{goal_id}", response_model=GoalRead)
def update_goal(
    goal_id: uuid.UUID,
    payload: GoalUpdate,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> GoalRead:
    try:
        goal = service.update_goal(
            db,
            current_user.id,
            goal_id,
            payload.name,
            payload.target_amount,
            payload.target_date,
            payload.clear_target_date,
        )
    except service.GoalNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="meta nao encontrada")

    return _to_read(db, current_user.id, goal)


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(
    goal_id: uuid.UUID, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> None:
    try:
        service.delete_goal(db, current_user.id, goal_id)
    except service.GoalNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="meta nao encontrada")


@router.post("/{goal_id}/contributions", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
def create_contribution(
    goal_id: uuid.UUID,
    payload: ContributionCreate,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> TransactionRead:
    try:
        transaction = service.create_contribution(
            db,
            current_user.id,
            goal_id,
            account_id=payload.account_id,
            category_id=payload.category_id,
            type=payload.type,
            amount=payload.amount,
            description=payload.description,
            occurred_at=payload.occurred_at,
        )
    except service.GoalNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="meta nao encontrada")
    except transactions_service.InvalidAccountError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="conta nao encontrada")
    except transactions_service.InvalidCategoryError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="categoria nao encontrada")
    except transactions_service.ArchivedAccountError:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, detail="conta arquivada nao aceita novos lancamentos"
        )

    return TransactionRead.model_validate(transaction)
