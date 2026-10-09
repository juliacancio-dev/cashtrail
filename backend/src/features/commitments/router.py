import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.dependencies import CurrentUser
from src.features.commitments import service
from src.features.commitments.models import CommitmentDirection
from src.features.commitments.schemas import (
    CommitmentCreate,
    CommitmentDetail,
    CommitmentList,
    CommitmentRead,
    CommitmentSummary,
    CommitmentTotals,
    CommitmentUpdate,
    SettlementCreate,
    SettlementRead,
    StatusFilter,
)

router = APIRouter(prefix="/commitments", tags=["commitments"])


def _read(view: service.CommitmentView) -> CommitmentRead:
    c = view.commitment
    return CommitmentRead(
        id=c.id,
        direction=c.direction,
        description=c.description,
        counterparty=c.counterparty,
        amount=c.amount,
        due_date=c.due_date,
        category_id=c.category_id,
        account_id=c.account_id,
        notes=c.notes,
        recurring_transaction_id=c.recurring_transaction_id,
        installment_group_id=c.installment_group_id,
        installment_number=c.installment_number,
        installment_count=c.installment_count,
        is_canceled=c.is_canceled,
        created_at=c.created_at,
        paid_amount=view.paid_amount,
        balance=view.balance,
        status=view.status,
    )


def _detail(view: service.CommitmentView, settlements) -> CommitmentDetail:
    return CommitmentDetail(
        **_read(view).model_dump(), settlements=[SettlementRead.model_validate(s) for s in settlements]
    )


def _not_found(exc: Exception) -> HTTPException:
    if isinstance(exc, service.CommitmentNotFoundError):
        return HTTPException(status.HTTP_404_NOT_FOUND, detail="compromisso nao encontrado")
    if isinstance(exc, service.SettlementNotFoundError):
        return HTTPException(status.HTTP_404_NOT_FOUND, detail="baixa nao encontrada")
    if isinstance(exc, service.InvalidAccountError):
        return HTTPException(status.HTTP_404_NOT_FOUND, detail="conta nao encontrada")
    return HTTPException(status.HTTP_404_NOT_FOUND, detail="categoria nao encontrada")


NOT_FOUND = (
    service.CommitmentNotFoundError,
    service.SettlementNotFoundError,
    service.InvalidAccountError,
    service.InvalidCategoryError,
)


@router.get("", response_model=CommitmentList)
def list_commitments(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    direction: CommitmentDirection | None = Query(default=None),
    status_filter: StatusFilter | None = Query(default=None, alias="status"),
    due_from: date | None = Query(default=None),
    due_to: date | None = Query(default=None),
    category_id: uuid.UUID | None = Query(default=None),
    account_id: uuid.UUID | None = Query(default=None),
) -> CommitmentList:
    views, totals = service.list_commitments(
        db, current_user.id, direction, status_filter, due_from, due_to, category_id, account_id
    )
    return CommitmentList(items=[_read(v) for v in views], totals=CommitmentTotals(**totals))


@router.get("/summary", response_model=CommitmentSummary)
def commitments_summary(current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]) -> CommitmentSummary:
    return CommitmentSummary(**service.summary(db, current_user.id))


@router.post("", response_model=list[CommitmentRead], status_code=status.HTTP_201_CREATED)
def create_commitment(
    payload: CommitmentCreate, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> list[CommitmentRead]:
    try:
        views = service.create_commitment(db, current_user.id, **payload.model_dump())
    except NOT_FOUND as exc:
        raise _not_found(exc)
    except service.ArchivedAccountError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail="conta arquivada nao aceita novos lancamentos")

    return [_read(v) for v in views]


@router.get("/{commitment_id}", response_model=CommitmentDetail)
def get_commitment(
    commitment_id: uuid.UUID, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> CommitmentDetail:
    try:
        view, settlements = service.get_commitment(db, current_user.id, commitment_id)
    except service.CommitmentNotFoundError as exc:
        raise _not_found(exc)

    return _detail(view, settlements)


@router.patch("/{commitment_id}", response_model=CommitmentRead)
def update_commitment(
    commitment_id: uuid.UUID,
    payload: CommitmentUpdate,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> CommitmentRead:
    try:
        view = service.update_commitment(
            db, current_user.id, commitment_id, payload.model_dump(exclude_unset=True)
        )
    except NOT_FOUND as exc:
        raise _not_found(exc)
    except service.ArchivedAccountError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail="conta arquivada nao aceita novos lancamentos")
    except service.CommitmentLockedError:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="compromisso pago ou cancelado nao pode ter valor ou vencimento alterados")
    except service.InvalidAmountError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail="o valor nao pode ser menor do que o ja pago")

    return _read(view)


@router.post("/{commitment_id}/cancel", response_model=CommitmentRead)
def cancel_commitment(
    commitment_id: uuid.UUID, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> CommitmentRead:
    try:
        view = service.cancel_commitment(db, current_user.id, commitment_id)
    except service.CommitmentNotFoundError as exc:
        raise _not_found(exc)
    except service.CommitmentLockedError:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="compromisso ja pago ou cancelado")

    return _read(view)


@router.post(
    "/{commitment_id}/settlements", response_model=CommitmentDetail, status_code=status.HTTP_201_CREATED
)
def settle_commitment(
    commitment_id: uuid.UUID,
    payload: SettlementCreate,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> CommitmentDetail:
    try:
        service.settle_commitment(
            db, current_user.id, commitment_id, payload.amount, payload.paid_at, payload.account_id
        )
        view, settlements = service.get_commitment(db, current_user.id, commitment_id)
    except NOT_FOUND as exc:
        raise _not_found(exc)
    except service.ArchivedAccountError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail="conta arquivada nao aceita novos lancamentos")
    except service.CommitmentLockedError:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="compromisso ja quitado ou cancelado")
    except service.InvalidAmountError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail="valor da baixa maior que o saldo em aberto")
    except service.AccountRequiredError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail="informe a conta da baixa")
    except service.FutureDateError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail="a data do pagamento nao pode estar no futuro")

    return _detail(view, settlements)


@router.delete("/{commitment_id}/settlements/{settlement_id}", response_model=CommitmentDetail)
def undo_settlement(
    commitment_id: uuid.UUID,
    settlement_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> CommitmentDetail:
    try:
        service.undo_settlement(db, current_user.id, commitment_id, settlement_id)
        view, settlements = service.get_commitment(db, current_user.id, commitment_id)
    except NOT_FOUND as exc:
        raise _not_found(exc)

    return _detail(view, settlements)
