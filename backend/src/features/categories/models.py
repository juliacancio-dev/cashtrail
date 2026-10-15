import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base

# Grupos do DRE pessoal (RF-032, Marco 10). Texto com CHECK, e não enum do Postgres:
# o projeto já teve problema duas vezes com enum novo em migration.
DRE_GROUPS = (
    "revenue",            # receitas
    "deduction",          # deduções (INSS, IR retido)
    "variable_expense",   # despesas variáveis
    "fixed_expense",      # despesas fixas
    "financial_expense",  # despesas financeiras (juros, tarifas)
    "financial_revenue",  # receitas financeiras (rendimentos)
)

# Classificação fiscal da DESPESA (Marco 14): só o que reduz a base do IRPF. Nulo = sem efeito fiscal.
IR_KINDS = (
    "deduction_health",     # saúde: dedutível sem limite
    "deduction_education",  # educação: limite por pessoa
    "deduction_pension",    # previdência privada PGBL: até 12% dos rendimentos tributáveis
)


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (
        CheckConstraint(
            "dre_group IS NULL OR dre_group IN ("
            + ", ".join(f"'{group}'" for group in DRE_GROUPS)
            + ")",
            name="ck_categories_dre_group",
        ),
        CheckConstraint(
            "ir_kind IS NULL OR ir_kind IN ("
            + ", ".join(f"'{kind}'" for kind in IR_KINDS)
            + ")",
            name="ck_categories_ir_kind",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    # Nulo = "Sem grupo": o DRE mostra essas categorias à parte (RB-028).
    dre_group: Mapped[str | None] = mapped_column(String(30), nullable=True)
    ir_kind: Mapped[str | None] = mapped_column(String(30), nullable=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
