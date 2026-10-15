import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, Numeric, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base

# String + CHECK, não enum nativo do Postgres (R-11.1).
POLICY_KINDS = ("life", "health", "auto", "home", "travel", "other")
PREMIUM_FREQUENCIES = ("monthly", "annual")


class InsurancePolicy(Base):
    """Apólice (RF-068): só METADADOS. Não guarda número de apólice nem documentos (R-15.5)."""

    __tablename__ = "insurance_policies"
    __table_args__ = (
        CheckConstraint("kind IN ('life', 'health', 'auto', 'home', 'travel', 'other')", name="ck_insurance_policies_kind"),
        CheckConstraint("premium_frequency IN ('monthly', 'annual')", name="ck_insurance_policies_frequency"),
        CheckConstraint("premium_amount > 0", name="ck_insurance_policies_premium"),
        CheckConstraint("coverage_amount IS NULL OR coverage_amount >= 0", name="ck_insurance_policies_coverage"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    kind: Mapped[str] = mapped_column(String(10), nullable=False)
    insurer: Mapped[str] = mapped_column(String(120), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    premium_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    premium_frequency: Mapped[str] = mapped_column(String(10), nullable=False)
    coverage_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    starts_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    # Fim da vigência / próxima renovação. Anual: também o vencimento do próximo prêmio.
    renews_on: Mapped[date] = mapped_column(Date, nullable=False)
    # Mensal: data da primeira cobrança da recorrência.
    first_due_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    asset_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("assets.id", ondelete="SET NULL"), index=True, nullable=True
    )
    payment_account_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=False
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False
    )
    # O prêmio mora num destes (RB-044, R-15.3): recorrência mensal ou conta a pagar do ciclo anual.
    recurring_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("recurring_transactions.id", ondelete="SET NULL"), nullable=True
    )
    commitment_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("commitments.id", ondelete="SET NULL"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
