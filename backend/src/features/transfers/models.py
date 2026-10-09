import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Numeric, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class Transfer(Base):
    """Transferência entre duas contas do mesmo usuário (RF-023).

    NÃO é receita nem despesa (RB-014): vive fora da tabela de lançamentos, então
    dashboard, orçamentos, metas e DRE nunca enxergam uma transferência.
    """

    __tablename__ = "transfers"
    __table_args__ = (
        CheckConstraint("from_account_id <> to_account_id", name="ck_transfers_different_accounts"),
        CheckConstraint("amount > 0", name="ck_transfers_amount_positive"),
        Index("ix_transfers_user_id_occurred_at", "user_id", "occurred_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    from_account_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("accounts.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    to_account_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("accounts.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    occurred_at: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
