import enum
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Index, Numeric, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class TransactionType(str, enum.Enum):
    INCOME = "income"
    EXPENSE = "expense"


class TransactionSource(str, enum.Enum):
    MANUAL = "manual"
    RECURRING = "recurring"
    IMPORT = "import"


class Transaction(Base):
    """Coluna de import_fitid do 10-data-model.md fica de fora até a slice
    statement_import existir (Marco 7) — evita campo sem uso real ainda.
    `goal_id` chegou no Marco 4 junto com `goals`; `source`/`recurring_transaction_id`
    chegaram no Marco 5 junto com `recurring`.
    """

    __tablename__ = "transactions"
    __table_args__ = (Index("ix_transactions_user_id_occurred_at", "user_id", "occurred_at"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("accounts.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("categories.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    goal_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("goals.id", ondelete="SET NULL"), index=True, nullable=True
    )
    recurring_transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("recurring_transactions.id", ondelete="SET NULL"), index=True, nullable=True
    )
    type: Mapped[TransactionType] = mapped_column(Enum(TransactionType, name="transaction_type"), nullable=False)
    source: Mapped[TransactionSource] = mapped_column(
        Enum(TransactionSource, name="transaction_source"),
        nullable=False,
        default=TransactionSource.MANUAL,
        server_default=TransactionSource.MANUAL.name,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    occurred_at: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
