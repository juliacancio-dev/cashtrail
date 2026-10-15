import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base

# String + CHECK, não enum nativo do Postgres (R-11.1).
ASSET_CLASSES = ("stock", "fii", "etf", "bdr", "fixed_income", "treasury", "fund", "crypto", "other")
QUOTE_SOURCES = ("brapi", "manual")
OPERATION_KINDS = ("buy", "sell", "income", "adjust")


class InvestmentAsset(Base):
    """Ativo da carteira (RF-049) guardado numa conta do tipo `investment`."""

    __tablename__ = "investment_assets"
    __table_args__ = (
        CheckConstraint(
            "asset_class IN ('stock', 'fii', 'etf', 'bdr', 'fixed_income', 'treasury', 'fund', 'crypto', 'other')",
            name="ck_investment_assets_asset_class",
        ),
        CheckConstraint("quote_source IN ('brapi', 'manual')", name="ck_investment_assets_quote_source"),
        UniqueConstraint("user_id", "account_id", "symbol", name="uq_investment_assets_user_account_symbol"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("accounts.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    # Nulo em renda fixa/manual. Maiúsculo (PETR4, HGLG11).
    symbol: Mapped[str | None] = mapped_column(String(20), nullable=True)
    asset_class: Mapped[str] = mapped_column(String(20), nullable=False)
    quote_source: Mapped[str] = mapped_column(String(10), nullable=False, default="manual")
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class InvestmentOperation(Base):
    """Compra, venda, provento ou ajuste de quantidade (RF-050 a RF-052).

    Compra e venda ligam-se à transferência real (caixa ↔ conta de investimento); venda com ganho/perda
    e provento ligam-se também ao lançamento financeiro. Desfazer apaga a operação E o que ela criou.
    """

    __tablename__ = "investment_operations"
    __table_args__ = (
        CheckConstraint("kind IN ('buy', 'sell', 'income', 'adjust')", name="ck_investment_operations_kind"),
        Index("ix_investment_operations_asset_id_occurred_at", "asset_id", "occurred_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    asset_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("investment_assets.id", ondelete="CASCADE"), nullable=False
    )
    kind: Mapped[str] = mapped_column(String(10), nullable=False)
    occurred_at: Mapped[date] = mapped_column(Date, nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False, default=Decimal("0"))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 6), nullable=False, default=Decimal("0"))
    fees: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0"))
    # Compra: custo total (inclui taxas). Venda: produto líquido. Provento: valor recebido.
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0"))
    cost_basis: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    gain: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    cash_account_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=True
    )
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("categories.id", ondelete="RESTRICT"), nullable=True
    )
    transfer_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("transfers.id", ondelete="RESTRICT"), unique=True, nullable=True
    )
    transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("transactions.id", ondelete="RESTRICT"), unique=True, nullable=True
    )
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class InvestmentQuote(Base):
    """Cotação diária guardada (RF-054). Acumula o histórico que o patrimônio usa em datas passadas."""

    __tablename__ = "investment_quotes"
    __table_args__ = (
        UniqueConstraint("asset_id", "quoted_on", name="uq_investment_quotes_asset_id_quoted_on"),
        CheckConstraint("price >= 0", name="ck_investment_quotes_price"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    asset_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("investment_assets.id", ondelete="CASCADE"), index=True, nullable=False
    )
    quoted_on: Mapped[date] = mapped_column(Date, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(14, 6), nullable=False)
    # brapi | manual | trade (preço de uma operação, usado quando ainda não há cotação do dia)
    source: Mapped[str] = mapped_column(String(10), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class QuoteRequestLog(Base):
    """Uma linha por requisição à fonte externa: base do teto mensal (decisão 3)."""

    __tablename__ = "quote_request_log"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    ok: Mapped[bool] = mapped_column(Boolean, nullable=False)
