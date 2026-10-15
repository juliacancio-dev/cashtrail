import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.dependencies import CurrentUser
from src.features.insurance import service
from src.features.insurance.schemas import (
    InsuranceSummary,
    PolicyCreate,
    PolicyRead,
    PolicyUpdate,
    RenewRequest,
    UninsuredAssetRead,
)

router = APIRouter(prefix="/insurance", tags=["insurance"])

ERRORS = {
    service.PolicyNotFoundError: (404, "apolice nao encontrada"),
    service.InvalidAccountError: (404, "conta nao encontrada"),
    service.InvalidCategoryError: (404, "categoria nao encontrada"),
    service.InvalidAssetError: (404, "bem nao encontrado"),
    service.ArchivedAccountError: (422, "conta arquivada nao aceita movimentacao"),
    service.InvalidPolicyError: (422, "tipo ou periodicidade invalidos"),
    service.PolicyInactiveError: (409, "apolice encerrada"),
}
HANDLED = tuple(ERRORS)


def _translate(exc: Exception) -> HTTPException:
    for cls, (code, message) in ERRORS.items():
        if isinstance(exc, cls):
            return HTTPException(code, detail=message)
    raise exc


def _read(view: service.PolicyView) -> PolicyRead:
    p = view.policy
    return PolicyRead(
        id=p.id,
        kind=p.kind,
        insurer=p.insurer,
        name=p.name,
        premium_amount=p.premium_amount,
        premium_frequency=p.premium_frequency,
        coverage_amount=p.coverage_amount,
        starts_on=p.starts_on,
        renews_on=p.renews_on,
        first_due_on=p.first_due_on,
        asset_id=p.asset_id,
        payment_account_id=p.payment_account_id,
        category_id=p.category_id,
        recurring_id=p.recurring_id,
        commitment_id=p.commitment_id,
        is_active=p.is_active,
        notes=p.notes,
        created_at=p.created_at,
        days_to_renewal=view.days_to_renewal,
        renewal_status=view.renewal_status,
    )


@router.get("", response_model=list[PolicyRead])
def list_policies(current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]) -> list[PolicyRead]:
    return [_read(v) for v in service.list_policies(db, current_user.id)]


@router.get("/summary", response_model=InsuranceSummary)
def get_summary(current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]) -> InsuranceSummary:
    s = service.summary(db, current_user.id)
    return InsuranceSummary(
        active_count=s.active_count,
        renewals_soon=[_read(v) for v in s.renewals_soon],
        overdue_renewals=[_read(v) for v in s.overdue_renewals],
        uninsured_assets=[UninsuredAssetRead(**a.__dict__) for a in s.uninsured_assets],
        monthly_cost=s.monthly_cost,
    )


@router.post("", response_model=PolicyRead, status_code=status.HTTP_201_CREATED)
def create_policy(
    payload: PolicyCreate, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> PolicyRead:
    try:
        return _read(service.create_policy(db, current_user.id, **payload.model_dump()))
    except HANDLED as exc:
        raise _translate(exc)


@router.patch("/{policy_id}", response_model=PolicyRead)
def update_policy(
    policy_id: uuid.UUID,
    payload: PolicyUpdate,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> PolicyRead:
    try:
        return _read(service.update_policy(db, current_user.id, policy_id, payload.model_dump(exclude_unset=True)))
    except HANDLED as exc:
        raise _translate(exc)


@router.post("/{policy_id}/renew", response_model=PolicyRead)
def renew_policy(
    policy_id: uuid.UUID,
    payload: RenewRequest,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> PolicyRead:
    try:
        return _read(service.renew_policy(db, current_user.id, policy_id, payload.premium_amount))
    except HANDLED as exc:
        raise _translate(exc)


@router.post("/{policy_id}/deactivate", response_model=PolicyRead)
def deactivate_policy(
    policy_id: uuid.UUID, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> PolicyRead:
    try:
        return _read(service.deactivate_policy(db, current_user.id, policy_id))
    except HANDLED as exc:
        raise _translate(exc)
