import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Numeric, String, Uuid, func, text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class AccountType(str, enum.Enum):
    CHECKING = "checking"
    SAVINGS = "savings"
    CREDIT_CARD = "credit_card"
    LOAN = "loan"
    INVESTMENT = "investment"


# Contas que NÃO são dinheiro em caixa: cartão, empréstimo/financiamento e investimento (R-11.3, RB-032).
# Um único predicado, usado por saldos, fluxo de caixa e dashboard.
NON_CASH_TYPES = (AccountType.CREDIT_CARD, AccountType.LOAN, AccountType.INVESTMENT)


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    type: Mapped[AccountType] = mapped_column(Enum(AccountType, name="account_type"), nullable=False)
    # Saldo da conta no início do uso do app (RF-031). Num cartão, valor negativo = dívida inicial.
    opening_balance: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0"), server_default=text("0"), nullable=False
    )
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
