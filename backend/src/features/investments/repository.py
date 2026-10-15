import uuid
from datetime import date, datetime

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from src.features.investments.models import (
    InvestmentAsset,
    InvestmentOperation,
    InvestmentQuote,
    QuoteRequestLog,
)


def list_assets(db: Session, user_id: uuid.UUID) -> list[InvestmentAsset]:
    return list(
        db.scalars(
            select(InvestmentAsset).where(InvestmentAsset.user_id == user_id).order_by(InvestmentAsset.name)
        )
    )


def get_asset(db: Session, asset_id: uuid.UUID, user_id: uuid.UUID) -> InvestmentAsset | None:
    """RNF-001: toda leitura já nasce filtrada por user_id, nunca só por id."""
    return db.scalar(
        select(InvestmentAsset).where(InvestmentAsset.id == asset_id, InvestmentAsset.user_id == user_id)
    )


def list_operations(
    db: Session, user_id: uuid.UUID, asset_id: uuid.UUID | None = None
) -> list[InvestmentOperation]:
    stmt = select(InvestmentOperation).where(InvestmentOperation.user_id == user_id)
    if asset_id is not None:
        stmt = stmt.where(InvestmentOperation.asset_id == asset_id)
    return list(db.scalars(stmt.order_by(InvestmentOperation.occurred_at, InvestmentOperation.created_at)))


def get_operation(
    db: Session, operation_id: uuid.UUID, asset_id: uuid.UUID, user_id: uuid.UUID
) -> InvestmentOperation | None:
    return db.scalar(
        select(InvestmentOperation).where(
            InvestmentOperation.id == operation_id,
            InvestmentOperation.asset_id == asset_id,
            InvestmentOperation.user_id == user_id,
        )
    )


def list_quotes(db: Session, user_id: uuid.UUID, asset_id: uuid.UUID | None = None) -> list[InvestmentQuote]:
    stmt = select(InvestmentQuote).where(InvestmentQuote.user_id == user_id)
    if asset_id is not None:
        stmt = stmt.where(InvestmentQuote.asset_id == asset_id)
    return list(db.scalars(stmt.order_by(InvestmentQuote.asset_id, InvestmentQuote.quoted_on)))


def get_quote_on(db: Session, asset_id: uuid.UUID, quoted_on: date, user_id: uuid.UUID) -> InvestmentQuote | None:
    return db.scalar(
        select(InvestmentQuote).where(
            InvestmentQuote.asset_id == asset_id,
            InvestmentQuote.quoted_on == quoted_on,
            InvestmentQuote.user_id == user_id,
        )
    )


def count_requests_since(db: Session, since: datetime) -> int:
    return int(db.scalar(select(func.count()).select_from(QuoteRequestLog).where(QuoteRequestLog.requested_at >= since)) or 0)


def users_with_auto_assets(db: Session) -> list[uuid.UUID]:
    rows = db.scalars(
        select(distinct(InvestmentAsset.user_id)).where(
            InvestmentAsset.quote_source == "brapi",
            InvestmentAsset.is_archived.is_(False),
            InvestmentAsset.symbol.is_not(None),
        )
    )
    return list(rows)


def add(db: Session, *rows: object) -> None:
    """Só adiciona e dá flush: o commit é do service, junto com o que as outras slices criaram."""
    db.add_all(rows)
    db.flush()


def delete(db: Session, row: object) -> None:
    db.delete(row)
    db.flush()
