import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.dependencies import CurrentUser
from src.features.transfers import service
from src.features.transfers.schemas import TransferCreate, TransferRead

router = APIRouter(prefix="/transfers", tags=["transfers"])


@router.get("", response_model=list[TransferRead])
def list_transfers(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    account_id: uuid.UUID | None = Query(default=None),
) -> list[TransferRead]:
    transfers = service.list_transfers(db, current_user.id, start_date, end_date, account_id)
    return [TransferRead.model_validate(t) for t in transfers]


@router.post("", response_model=TransferRead, status_code=status.HTTP_201_CREATED)
def create_transfer(
    payload: TransferCreate, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> TransferRead:
    try:
        transfer = service.create_transfer(db, current_user.id, **payload.model_dump())
    except service.InvalidAccountError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="conta nao encontrada")
    except service.ArchivedAccountError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail="conta arquivada nao aceita movimentacao")
    except service.SameAccountError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail="origem e destino devem ser contas diferentes")
    except service.FutureDateError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail="a data da transferencia nao pode estar no futuro")

    return TransferRead.model_validate(transfer)


@router.get("/{transfer_id}", response_model=TransferRead)
def get_transfer(
    transfer_id: uuid.UUID, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> TransferRead:
    try:
        transfer = service.get_transfer(db, current_user.id, transfer_id)
    except service.TransferNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="transferencia nao encontrada")

    return TransferRead.model_validate(transfer)


@router.delete("/{transfer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transfer(
    transfer_id: uuid.UUID, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> Response:
    try:
        service.delete_transfer(db, current_user.id, transfer_id)
    except service.TransferNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="transferencia nao encontrada")

    return Response(status_code=status.HTTP_204_NO_CONTENT)
