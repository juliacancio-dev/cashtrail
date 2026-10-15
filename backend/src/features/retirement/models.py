import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Numeric, SmallInteger, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class RetirementPlan(Base):
    """Premissas do plano de independência financeira (RF-072): um por usuário.

    Tudo em VALORES REAIS (RB-045): a renda desejada é em poder de compra de hoje e o retorno é acima da inflação.
    """

    __tablename__ = "retirement_plans"
    __table_args__ = (
        CheckConstraint("current_age >= 0 AND current_age <= 120", name="ck_retirement_plans_current_age"),
        CheckConstraint("target_age > current_age AND target_age <= 120", name="ck_retirement_plans_target_age"),
        CheckConstraint("monthly_income_wanted > 0", name="ck_retirement_plans_income"),
        CheckConstraint("withdrawal_rate > 0 AND withdrawal_rate <= 0.2", name="ck_retirement_plans_withdrawal"),
        CheckConstraint("real_return_annual >= -0.2 AND real_return_annual <= 0.3", name="ck_retirement_plans_return"),
        CheckConstraint("monthly_contribution >= 0", name="ck_retirement_plans_contribution"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    current_age: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    target_age: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    monthly_income_wanted: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    # Benefício público esperado (INSS), informado pelo usuário: o sistema não o calcula (decisão 3).
    public_benefit_monthly: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0"))
    # Frações: 0.04 = 4%. Premissas editáveis (RB-048).
    real_return_annual: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False)
    withdrawal_rate: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False)
    monthly_contribution: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0"))
    include_assets: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
