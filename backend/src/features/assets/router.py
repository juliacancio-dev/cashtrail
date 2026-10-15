import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.dependencies import CurrentUser
from src.features.assets import service
from src.features.assets.schemas import (
    AssetCreate,
    AssetDetail,
    AssetRead,
    AssetUpdate,
    ValuationCreate,
    ValuationRead,
)

router = APIRouter(prefix="/assets", tags=["assets"])

ERRORS = {
    service.AssetNotFoundError: (404, "bem nao encontrado"),
    service.ValuationNotFoundError: (404, "avaliacao nao encontrada"),
    service.InvalidDebtError: (404, "divida nao encontrada"),
    service.DebtAlreadyLinkedError: (409, "esta divida ja financia outro bem"),
    service.InvalidKindError: (422, "tipo de bem invalido"),
    service.FutureDateError: (422, "a data nao pode estar no futuro"),
    service.LastValuationError: (409, "o bem precisa manter ao menos uma avaliacao"),
}
HANDLED = tuple(ERRORS)


def _translate(exc: Exception) -> HTTPException:
    for cls, (code, message) in ERRORS.items():
        if isinstance(exc, cls):
            return HTTPException(code, detail=message)
    raise exc


def _read(view: service.AssetView) -> dict:
    a = view.asset
    return dict(
        id=a.id,
        name=a.name,
        kind=a.kind,
        acquired_at=a.acquired_at,
        acquisition_value=a.acquisition_value,
        debt_id=a.debt_id,
        disposed_at=a.disposed_at,
        value=view.value,
        valued_at=view.valued_at,
        is_stale=view.is_stale,
    )


def _detail(db: Session, user_id: uuid.UUID, asset_id: uuid.UUID) -> AssetDetail:
    view, valuations = service.get_detail(db, user_id, asset_id)
    ordered = sorted(valuations, key=lambda v: v.valued_at, reverse=True)
    return AssetDetail(**_read(view), valuations=[ValuationRead.model_validate(v) for v in ordered])


@router.get("", response_model=list[AssetRead])
def list_assets(current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]) -> list[AssetRead]:
    return [AssetRead(**_read(v)) for v in service.list_views(db, current_user.id)]


@router.post("", response_model=AssetDetail, status_code=status.HTTP_201_CREATED)
def create_asset(
    payload: AssetCreate, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> AssetDetail:
    try:
        view = service.create_asset(db, current_user.id, **payload.model_dump())
        return _detail(db, current_user.id, view.asset.id)
    except HANDLED as exc:
        raise _translate(exc)


@router.get("/{asset_id}", response_model=AssetDetail)
def get_asset(asset_id: uuid.UUID, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]) -> AssetDetail:
    try:
        return _detail(db, current_user.id, asset_id)
    except HANDLED as exc:
        raise _translate(exc)


@router.patch("/{asset_id}", response_model=AssetDetail)
def update_asset(
    asset_id: uuid.UUID,
    payload: AssetUpdate,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> AssetDetail:
    try:
        service.update_asset(db, current_user.id, asset_id, payload.model_dump(exclude_unset=True))
        return _detail(db, current_user.id, asset_id)
    except HANDLED as exc:
        raise _translate(exc)


@router.post("/{asset_id}/valuations", response_model=AssetDetail, status_code=status.HTTP_201_CREATED)
def set_valuation(
    asset_id: uuid.UUID,
    payload: ValuationCreate,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> AssetDetail:
    try:
        service.set_valuation(db, current_user.id, asset_id, payload.valued_at, payload.value, payload.note)
        return _detail(db, current_user.id, asset_id)
    except HANDLED as exc:
        raise _translate(exc)


@router.delete("/{asset_id}/valuations/{valuation_id}", response_model=AssetDetail)
def delete_valuation(
    asset_id: uuid.UUID,
    valuation_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> AssetDetail:
    try:
        service.delete_valuation(db, current_user.id, asset_id, valuation_id)
        return _detail(db, current_user.id, asset_id)
    except HANDLED as exc:
        raise _translate(exc)
