import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, Index, Numeric, SmallInteger, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base

# String + CHECK, não enum nativo do Postgres (R-11.1: enums nativos já deram problema de migração).
DEBT_SYSTEMS = ("price", "sac", "zero")
AMORTIZATION_MODES = ("reduce_term", "reduce_installment", "payoff")


class Debt(Base):
    """Configuração de uma dívida (RF-032) sobre uma conta do tipo `loan`.

    A conta continua sendo da slice accounts; o saldo devedor é o negativo do saldo dela.
    """

    __tablename__ = "debts"
    __table_args__ = (
        CheckConstraint("system IN ('price', 'sac', 'zero')", name="ck_debts_system"),
        CheckConstraint("principal > 0", name="ck_debts_principal"),
        CheckConstraint("monthly_rate >= 0", name="ck_debts_monthly_rate"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("accounts.id", ondelete="RESTRICT"), unique=True, nullable=False
    )
    creditor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    principal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    contracted_at: Mapped[date] = mapped_column(Date, nullable=False)
    installments: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    system: Mapped[str] = mapped_column(String(10), nullable=False)
    # Em PERCENTUAL ao mês (1.99 = 1,99% a.m.), como o banco informa.
    monthly_rate: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False, default=Decimal("0"))
    first_due_date: Mapped[date] = mapped_column(Date, nullable=False)
    payment_account_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=True
    )
    # Categoria dos encargos (juros, IOF, seguro): a despesa de cada baixa nasce nela.
    interest_category_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DebtInstallment(Base):
    """Liga uma parcela (Commitment) ao cronograma da dívida e guarda a parte de principal dela.

    Os encargos da parcela = valor do compromisso − principal_part, então editar o valor da
    parcela mexe só nos encargos (RF-034).
    """

    __tablename__ = "debt_installments"
    __table_args__ = (Index("ix_debt_installments_debt_id_number", "debt_id", "number"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    debt_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("debts.id", ondelete="CASCADE"), nullable=False
    )
    number: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    commitment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("commitments.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    principal_part: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    # Substituída por um recálculo (amortização extra): fica no histórico, fora do cronograma.
    is_superseded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DebtAmortization(Base):
    """Pagamento extra de principal (RF-040) ou quitação (RF-038)."""

    __tablename__ = "debt_amortizations"
    __table_args__ = (
        CheckConstraint("mode IN ('reduce_term', 'reduce_installment', 'payoff')", name="ck_debt_amortizations_mode"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    debt_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("debts.id", ondelete="CASCADE"), index=True, nullable=False
    )
    transfer_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("transfers.id", ondelete="RESTRICT"), unique=True, nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    paid_at: Mapped[date] = mapped_column(Date, nullable=False)
    mode: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
