import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.features.assets.models import Asset, AssetValuation


def list_assets(db: Session, user_id: uuid.UUID) -> list[Asset]:
    return list(db.scalars(select(Asset).where(Asset.user_id == user_id).order_by(Asset.created_at, Asset.name)))


def get_asset(db: Session, asset_id: uuid.UUID, user_id: uuid.UUID) -> Asset | None:
    """RNF-001: toda leitura já nasce filtrada por user_id, nunca só por id."""
    return db.scalar(select(Asset).where(Asset.id == asset_id, Asset.user_id == user_id))


def list_valuations(db: Session, user_id: uuid.UUID, asset_id: uuid.UUID | None = None) -> list[AssetValuation]:
    stmt = select(AssetValuation).where(AssetValuation.user_id == user_id)
    if asset_id is not None:
        stmt = stmt.where(AssetValuation.asset_id == asset_id)
    return list(db.scalars(stmt.order_by(AssetValuation.asset_id, AssetValuation.valued_at)))


def get_valuation_on(db: Session, asset_id: uuid.UUID, valued_at: date, user_id: uuid.UUID) -> AssetValuation | None:
    return db.scalar(
        select(AssetValuation).where(
            AssetValuation.asset_id == asset_id,
            AssetValuation.valued_at == valued_at,
            AssetValuation.user_id == user_id,
        )
    )


def get_valuation(
    db: Session, valuation_id: uuid.UUID, asset_id: uuid.UUID, user_id: uuid.UUID
) -> AssetValuation | None:
    return db.scalar(
        select(AssetValuation).where(
            AssetValuation.id == valuation_id,
            AssetValuation.asset_id == asset_id,
            AssetValuation.user_id == user_id,
        )
    )


def add(db: Session, row: object) -> None:
    db.add(row)
    db.flush()


def delete(db: Session, row: object) -> None:
    db.delete(row)
    db.flush()
