import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.features.assets import repository
from src.features.assets.models import ASSET_KINDS, Asset, AssetValuation
from src.features.debts import service as debts_service

ZERO = Decimal("0.00")
STALE_DAYS = 365


class AssetNotFoundError(Exception):
    pass


class ValuationNotFoundError(Exception):
    pass


class InvalidDebtError(Exception):
    pass


class DebtAlreadyLinkedError(Exception):
    """Cada dívida financia no máximo um bem."""


class InvalidKindError(Exception):
    pass


class FutureDateError(Exception):
    pass


class LastValuationError(Exception):
    """O bem precisa manter ao menos uma avaliação."""


@dataclass(frozen=True)
class AssetView:
    asset: Asset
    value: Decimal  # na data pedida (zero antes da 1ª avaliação ou depois da baixa)
    valued_at: date | None  # data da avaliação usada
    is_stale: bool  # última avaliação com mais de 12 meses (R-12.1)


def value_on(asset: Asset, valuations: list[AssetValuation], on: date) -> tuple[Decimal, date | None]:
    """RB-030: antes da primeira avaliação (ou depois da baixa) o bem vale zero."""
    if asset.disposed_at is not None and on >= asset.disposed_at:
        return ZERO, None
    candidates = [v for v in valuations if v.valued_at <= on]
    if not candidates:
        return ZERO, None
    latest = max(candidates, key=lambda v: v.valued_at)
    return latest.value, latest.valued_at


def _check_debt(db: Session, user_id: uuid.UUID, debt_id: uuid.UUID, asset_id: uuid.UUID | None) -> None:
    if not debts_service.debt_exists(db, user_id, debt_id):
        raise InvalidDebtError(debt_id)
    for other in repository.list_assets(db, user_id):
        if other.debt_id == debt_id and other.id != asset_id:
            raise DebtAlreadyLinkedError(debt_id)


def list_views(db: Session, user_id: uuid.UUID, on: date | None = None) -> list[AssetView]:
    on = on or date.today()
    by_asset: dict[uuid.UUID, list[AssetValuation]] = {}
    for valuation in repository.list_valuations(db, user_id):
        by_asset.setdefault(valuation.asset_id, []).append(valuation)

    views: list[AssetView] = []
    for asset in repository.list_assets(db, user_id):
        value, valued_at = value_on(asset, by_asset.get(asset.id, []), on)
        stale = (
            valued_at is not None and asset.disposed_at is None and (on - valued_at).days > STALE_DAYS
        )
        views.append(AssetView(asset, value, valued_at, stale))
    return views


def get_asset(db: Session, user_id: uuid.UUID, asset_id: uuid.UUID) -> Asset:
    asset = repository.get_asset(db, asset_id, user_id)
    if asset is None:
        raise AssetNotFoundError(asset_id)
    return asset


def get_detail(
    db: Session, user_id: uuid.UUID, asset_id: uuid.UUID, on: date | None = None
) -> tuple[AssetView, list[AssetValuation]]:
    on = on or date.today()
    asset = get_asset(db, user_id, asset_id)
    valuations = repository.list_valuations(db, user_id, asset.id)
    value, valued_at = value_on(asset, valuations, on)
    stale = valued_at is not None and asset.disposed_at is None and (on - valued_at).days > STALE_DAYS
    return AssetView(asset, value, valued_at, stale), valuations


def create_asset(
    db: Session,
    user_id: uuid.UUID,
    name: str,
    kind: str,
    acquired_at: date | None,
    acquisition_value: Decimal | None,
    current_value: Decimal,
    valued_at: date | None,
    debt_id: uuid.UUID | None,
    today: date | None = None,
) -> AssetView:
    today = today or date.today()
    if kind not in ASSET_KINDS:
        raise InvalidKindError(kind)
    valued_at = valued_at or today
    if valued_at > today:
        raise FutureDateError(valued_at)
    if debt_id is not None:
        _check_debt(db, user_id, debt_id, None)

    asset = Asset(
        user_id=user_id,
        name=name,
        kind=kind,
        acquired_at=acquired_at,
        acquisition_value=acquisition_value,
        debt_id=debt_id,
    )
    repository.add(db, asset)
    repository.add(
        db, AssetValuation(user_id=user_id, asset_id=asset.id, valued_at=valued_at, value=current_value)
    )
    db.commit()
    return get_detail(db, user_id, asset.id, today)[0]


def update_asset(
    db: Session, user_id: uuid.UUID, asset_id: uuid.UUID, changes: dict, today: date | None = None
) -> AssetView:
    """`debt_id: null` desvincula; `disposed_at: null` reativa o bem."""
    today = today or date.today()
    asset = get_asset(db, user_id, asset_id)
    if "kind" in changes and changes["kind"] not in ASSET_KINDS:
        raise InvalidKindError(changes["kind"])
    if changes.get("debt_id") is not None:
        _check_debt(db, user_id, changes["debt_id"], asset.id)
    if changes.get("disposed_at") is not None and changes["disposed_at"] > today:
        raise FutureDateError(changes["disposed_at"])

    for field in ("name", "kind", "acquired_at", "acquisition_value", "debt_id", "disposed_at"):
        if field in changes:
            setattr(asset, field, changes[field])
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise DebtAlreadyLinkedError(changes.get("debt_id"))
    return get_detail(db, user_id, asset.id, today)[0]


def set_valuation(
    db: Session,
    user_id: uuid.UUID,
    asset_id: uuid.UUID,
    valued_at: date | None,
    value: Decimal,
    note: str | None,
    today: date | None = None,
) -> AssetView:
    """RF-042: uma avaliação por data; informar a mesma data de novo corrige o valor."""
    today = today or date.today()
    asset = get_asset(db, user_id, asset_id)
    valued_at = valued_at or today
    if valued_at > today:
        raise FutureDateError(valued_at)

    existing = repository.get_valuation_on(db, asset.id, valued_at, user_id)
    if existing is not None:
        existing.value = value
        existing.note = note
    else:
        repository.add(db, AssetValuation(user_id=user_id, asset_id=asset.id, valued_at=valued_at, value=value, note=note))
    db.commit()
    return get_detail(db, user_id, asset.id, today)[0]


def delete_valuation(
    db: Session, user_id: uuid.UUID, asset_id: uuid.UUID, valuation_id: uuid.UUID, today: date | None = None
) -> AssetView:
    asset = get_asset(db, user_id, asset_id)
    valuation = repository.get_valuation(db, valuation_id, asset.id, user_id)
    if valuation is None:
        raise ValuationNotFoundError(valuation_id)
    if len(repository.list_valuations(db, user_id, asset.id)) <= 1:
        raise LastValuationError(asset_id)
    repository.delete(db, valuation)
    db.commit()
    return get_detail(db, user_id, asset.id, today)[0]
