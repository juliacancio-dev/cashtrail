import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.dependencies import CurrentUser
from src.features.recurring import service
from src.features.recurring.schemas import RecurringCreate, RecurringRead, RecurringUpdate

router = APIRouter(prefix="/recurring", tags=["recurring"])


@router.get("", response_model=list[RecurringRead])
def list_recurring(
    current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> list[RecurringRead]:
    items = service.list_recurring(db, current_user.id)
    return [RecurringRead.model_validate(r) for r in items]


@router.post("", response_model=RecurringRead, status_code=status.HTTP_201_CREATED)
def create_recurring(
    payload: RecurringCreate, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> RecurringRead:
    try:
        recurring = service.create_recurring(
            db,
            current_user.id,
            account_id=payload.account_id,
            category_id=payload.category_id,
            type=payload.type,
            amount=payload.amount,
            description=payload.description,
            frequency=payload.frequency,
            next_occurrence_date=payload.next_occurrence_date,
        )
    except service.InvalidAccountError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="conta nao encontrada")
    except service.InvalidCategoryError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="categoria nao encontrada")
    except service.ArchivedAccountError:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, detail="conta arquivada nao aceita novos lancamentos"
        )

    return RecurringRead.model_validate(recurring)


@router.get("/{recurring_id}", response_model=RecurringRead)
def get_recurring(
    recurring_id: uuid.UUID, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> RecurringRead:
    try:
        recurring = service.get_recurring(db, current_user.id, recurring_id)
    except service.RecurringNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="recorrencia nao encontrada")

    return RecurringRead.model_validate(recurring)


@router.patch("/{recurring_id}", response_model=RecurringRead)
def update_recurring(
    recurring_id: uuid.UUID,
    payload: RecurringUpdate,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> RecurringRead:
    try:
        recurring = service.update_recurring(
            db, current_user.id, recurring_id, payload.amount, payload.description, payload.frequency
        )
    except service.RecurringNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="recorrencia nao encontrada")

    return RecurringRead.model_validate(recurring)


@router.post("/{recurring_id}/deactivate", response_model=RecurringRead)
def deactivate_recurring(
    recurring_id: uuid.UUID, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> RecurringRead:
    try:
        recurring = service.deactivate_recurring(db, current_user.id, recurring_id)
    except service.RecurringNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="recorrencia nao encontrada")

    return RecurringRead.model_validate(recurring)
