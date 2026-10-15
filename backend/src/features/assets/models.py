import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Numeric, String, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base

# String + CHECK, não enum nativo do Postgres (R-11.1: enums nativos já deram problema de migração).
ASSET_KINDS = ("real_estate", "vehicle", "other")


class Asset(Base):
    """Bem do patrimônio (RF-041): imóvel, veículo etc. O valor vive em AssetValuation."""

    __tablename__ = "assets"
    __table_args__ = (
        CheckConstraint("kind IN ('real_estate', 'vehicle', 'other')", name="ck_assets_kind"),
        CheckConstraint("acquisition_value IS NULL OR acquisition_value >= 0", name="ck_assets_acquisition_value"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    acquired_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    acquisition_value: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    # Financiamento do bem (RF-043): só leitura agregada, não muda nenhum total. Um bem por dívida.
    debt_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("debts.id", ondelete="SET NULL"), unique=True, nullable=True
    )
    # Venda ou baixa: a partir desta data o bem vale zero, e o histórico anterior continua correto.
    disposed_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AssetValuation(Base):
    """Avaliação do bem numa data (RF-042). Valor "em uma data" = última avaliação até ela."""

    __tablename__ = "asset_valuations"
    __table_args__ = (
        UniqueConstraint("asset_id", "valued_at", name="uq_asset_valuations_asset_id_valued_at"),
        CheckConstraint("value >= 0", name="ck_asset_valuations_value"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    asset_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("assets.id", ondelete="CASCADE"), index=True, nullable=False
    )
    valued_at: Mapped[date] = mapped_column(Date, nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
