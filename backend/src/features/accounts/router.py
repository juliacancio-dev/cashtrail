import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.dependencies import CurrentUser
from src.features.accounts import service
from src.features.accounts.schemas import AccountCreate, AccountRead, AccountUpdate

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("", response_model=list[AccountRead])
def list_accounts(
    current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> list[AccountRead]:
    accounts = service.list_accounts(db, current_user.id)
    return [AccountRead.model_validate(a) for a in accounts]


@router.post("", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
def create_account(
    payload: AccountCreate, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> AccountRead:
    account = service.create_account(
        db, current_user.id, payload.name, payload.type, payload.opening_balance
    )
    return AccountRead.model_validate(account)


@router.get("/{account_id}", response_model=AccountRead)
def get_account(
    account_id: uuid.UUID, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> AccountRead:
    try:
        account = service.get_account(db, current_user.id, account_id)
    except service.AccountNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="conta nao encontrada")

    return AccountRead.model_validate(account)


@router.patch("/{account_id}", response_model=AccountRead)
def update_account(
    account_id: uuid.UUID,
    payload: AccountUpdate,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> AccountRead:
    try:
        # `null` explícito não limpa nada nestes campos: ignora e mantém o valor atual.
        changes = {k: v for k, v in payload.model_dump(exclude_unset=True).items() if v is not None}
        account = service.update_account(db, current_user.id, account_id, changes)
    except service.AccountNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="conta nao encontrada")

    return AccountRead.model_validate(account)


@router.post("/{account_id}/archive", response_model=AccountRead)
def archive_account(
    account_id: uuid.UUID, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> AccountRead:
    try:
        account = service.archive_account(db, current_user.id, account_id)
    except service.AccountNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="conta nao encontrada")

    return AccountRead.model_validate(account)
