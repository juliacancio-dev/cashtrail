import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Numeric, SmallInteger, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class CreditCard(Base):
    """Configuração de cartão (RF-024) sobre uma conta do tipo `credit_card`.

    A conta continua sendo da slice accounts; aqui ficam só as regras de fatura.
    """

    __tablename__ = "credit_cards"
    __table_args__ = (
        CheckConstraint("closing_day BETWEEN 1 AND 31", name="ck_credit_cards_closing_day"),
        CheckConstraint("due_day BETWEEN 1 AND 31", name="ck_credit_cards_due_day"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("accounts.id", ondelete="RESTRICT"), unique=True, nullable=False
    )
    closing_day: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    due_day: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    credit_limit: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    default_payment_account_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CardPurchase(Base):
    """Liga um lançamento da conta do cartão à fatura ESCOLHIDA para ele (RF-025).

    Sem linha aqui, a fatura do lançamento é calculada pela data (RB-019): compras
    antigas e as lançadas direto em /transactions continuam funcionando.
    """

    __tablename__ = "card_purchases"
    __table_args__ = (Index("ix_card_purchases_credit_card_id_closing", "credit_card_id", "invoice_closing_date"),)

    transaction_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("transactions.id", ondelete="CASCADE"), primary_key=True
    )
    credit_card_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("credit_cards.id", ondelete="CASCADE"), nullable=False
    )
    # A fatura é identificada pela sua data de fechamento.
    invoice_closing_date: Mapped[date] = mapped_column(Date, nullable=False)


class CardInvoicePayment(Base):
    """Pagamento (total ou parcial) de uma fatura. Cada um aponta para a transferência
    que criou; o saldo da fatura é derivado (compras − estornos − pagamentos)."""

    __tablename__ = "card_invoice_payments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    credit_card_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("credit_cards.id", ondelete="CASCADE"), index=True, nullable=False
    )
    invoice_closing_date: Mapped[date] = mapped_column(Date, nullable=False)
    # RESTRICT: a transferência não some sozinha; desfazer o pagamento apaga o vínculo primeiro.
    transfer_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("transfers.id", ondelete="RESTRICT"), unique=True, nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    paid_at: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
