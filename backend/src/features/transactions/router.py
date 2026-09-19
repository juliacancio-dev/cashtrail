import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.dependencies import CurrentUser
from src.features.transactions import service
from src.features.transactions.schemas import TransactionCreate, TransactionRead

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("", response_model=list[TransactionRead])
def list_transactions(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
) -> list[TransactionRead]:
    transactions = service.list_transactions(db, current_user.id, start_date, end_date)
    return [TransactionRead.model_validate(t) for t in transactions]


@router.post("", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
def create_transaction(
    payload: TransactionCreate, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> TransactionRead:
    try:
        transaction = service.create_transaction(
            db,
            current_user.id,
            account_id=payload.account_id,
            category_id=payload.category_id,
            type=payload.type,
            amount=payload.amount,
            description=payload.description,
            occurred_at=payload.occurred_at,
        )
    except service.InvalidAccountError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="conta nao encontrada")
    except service.InvalidCategoryError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="categoria nao encontrada")
    except service.ArchivedAccountError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail="conta arquivada nao aceita novos lancamentos")

    return TransactionRead.model_validate(transaction)


@router.get("/{transaction_id}", response_model=TransactionRead)
def get_transaction(
    transaction_id: uuid.UUID, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> TransactionRead:
    try:
        transaction = service.get_transaction(db, current_user.id, transaction_id)
    except service.TransactionNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="lancamento nao encontrado")

    return TransactionRead.model_validate(transaction)
