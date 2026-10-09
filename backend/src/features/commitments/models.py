import enum
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, Enum, ForeignKey, Numeric, SmallInteger, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class CommitmentDirection(str, enum.Enum):
    PAYABLE = "payable"
    RECEIVABLE = "receivable"


class Commitment(Base):
    """Conta a pagar ou a receber (RF-014). Representa uma obrigação com vencimento;
    o dinheiro só vira lançamento realizado quando há uma baixa (CommitmentSettlement).
    """

    __tablename__ = "commitments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    direction: Mapped[CommitmentDirection] = mapped_column(
        Enum(CommitmentDirection, name="commitment_direction"), nullable=False
    )
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    # Favorecido em texto livre (decisão 6 do desenho): vira entidade só se houver necessidade real.
    counterparty: Mapped[str | None] = mapped_column(String(255), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    category_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("categories.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    # Conta prevista para o pagamento; a conta real é informada na baixa.
    account_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("accounts.id", ondelete="RESTRICT"), index=True, nullable=True
    )
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    # Preenchido só quando o compromisso foi gerado por uma recorrência (Marco 8, etapa 6).
    # Mesmo padrão de transactions.recurring_transaction_id: FK sem importar a slice recurring.
    recurring_transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("recurring_transactions.id", ondelete="SET NULL"), index=True, nullable=True
    )
    # Parcelas são compromissos independentes ligados por um grupo (decisão 2).
    installment_group_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, index=True, nullable=True)
    installment_number: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    installment_count: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    # Parcela de uma dívida (Marco 11): a baixa e a edição passam pela slice debts, que separa
    # principal de encargos. FK só por coluna, sem importar a slice debts (mesmo padrão de recurring).
    debt_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("debts.id", ondelete="SET NULL"), index=True, nullable=True
    )
    is_canceled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CommitmentSettlement(Base):
    """Baixa (pagamento ou recebimento) de um compromisso. Cada baixa aponta para o
    lançamento realizado que criou; o saldo do compromisso é derivado da soma delas.
    """

    __tablename__ = "commitment_settlements"
    __table_args__ = (
        CheckConstraint(
            "transaction_id IS NOT NULL OR transfer_id IS NOT NULL", name="ck_commitment_settlements_target"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    commitment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("commitments.id", ondelete="CASCADE"), index=True, nullable=False
    )
    # RESTRICT: o lançamento não some sozinho; desfazer a baixa apaga a baixa primeiro.
    # Nulo quando a baixa foi só transferência (parcela de dívida sem encargos).
    transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("transactions.id", ondelete="RESTRICT"), unique=True, nullable=True
    )
    # Preenchido quando parte da baixa foi uma transferência (principal de dívida, Marco 11).
    transfer_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("transfers.id", ondelete="RESTRICT"), unique=True, nullable=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    paid_at: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
