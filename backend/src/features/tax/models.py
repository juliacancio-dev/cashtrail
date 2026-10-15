import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, SmallInteger, String, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base

# Tipos de linha do informe de rendimentos. String + CHECK (sem enum nativo, R-11.1).
STATEMENT_KINDS = ("salary", "other_taxable", "thirteenth", "plr", "exclusive_other", "exempt")


class TaxYearSettings(Base):
    """Dados do ano que não vêm dos lançamentos (RF-060): só a QUANTIDADE de dependentes, sem CPF (RB-043)."""

    __tablename__ = "tax_year_settings"
    __table_args__ = (
        UniqueConstraint("user_id", "year", name="uq_tax_year_settings_user_year"),
        CheckConstraint("dependents_count >= 0 AND dependents_count <= 20", name="ck_tax_year_settings_dependents"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    year: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    dependents_count: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)


class TaxIncomeStatement(Base):
    """Linha do informe de rendimentos digitada do documento oficial (RF-061).

    O salário que cai na conta é líquido: bruto, INSS e IRRF só existem no informe. Não guarda CPF/CNPJ
    da fonte pagadora (RB-043): só o nome para o usuário se orientar.
    """

    __tablename__ = "tax_income_statements"
    __table_args__ = (
        CheckConstraint(
            "kind IN ('salary', 'other_taxable', 'thirteenth', 'plr', 'exclusive_other', 'exempt')",
            name="ck_tax_income_statements_kind",
        ),
        CheckConstraint(
            "gross_income >= 0 AND social_security >= 0 AND withheld_tax >= 0",
            name="ck_tax_income_statements_amounts",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    year: Mapped[int] = mapped_column(SmallInteger, index=True, nullable=False)
    payer_name: Mapped[str] = mapped_column(String(120), nullable=False)
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    gross_income: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0"))
    social_security: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0"))
    withheld_tax: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0"))
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
