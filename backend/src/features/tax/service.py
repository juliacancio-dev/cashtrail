import uuid
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.features.assets import service as assets_service
from src.features.categories import service as categories_service
from src.features.investments import service as investments_service
from src.features.reports import net_worth as net_worth_report
from src.features.tax import calc
from src.features.tax.models import STATEMENT_KINDS, TaxIncomeStatement, TaxYearSettings
from src.features.tax.parameters import TaxParameters, UnsupportedYearError, available_years, load
from src.features.transactions import service as transactions_service
from src.features.transactions.models import TransactionType

ZERO = Decimal("0.00")
TAXABLE_KINDS = ("salary", "other_taxable")


class StatementNotFoundError(Exception):
    pass


class InvalidKindError(Exception):
    pass


class InvalidYearError(Exception):
    pass


__all__ = ["UnsupportedYearError", "available_years"]


@dataclass(frozen=True)
class AssetRight:
    group: str  # Contas | Investimentos | Bens | Dívidas
    name: str
    amount: Decimal  # custo (RB-041), não valor de mercado
    note: str | None = None


@dataclass
class Dossier:
    year: int
    as_of: date
    parameters: TaxParameters
    dependents: int
    statements: list[TaxIncomeStatement]
    totals_by_kind: dict[str, dict[str, Decimal]]
    estimate: calc.AnnualEstimate
    variable_income: list[calc.MonthResult]
    day_trade_flags: list[str]
    assets_and_rights: list[AssetRight]
    debts: list[AssetRight]
    untagged_expense_categories: int
    warnings: list[str] = field(default_factory=list)


def _check_year(year: int, today: date) -> None:
    if year < 2000 or year > today.year:
        raise InvalidYearError(year)


# ---------- configuração e informes ----------

def get_dependents(db: Session, user_id: uuid.UUID, year: int) -> int:
    row = db.scalar(select(TaxYearSettings).where(TaxYearSettings.user_id == user_id, TaxYearSettings.year == year))
    return row.dependents_count if row else 0


def set_dependents(db: Session, user_id: uuid.UUID, year: int, count: int, today: date | None = None) -> int:
    _check_year(year, today or date.today())
    row = db.scalar(select(TaxYearSettings).where(TaxYearSettings.user_id == user_id, TaxYearSettings.year == year))
    if row is None:
        row = TaxYearSettings(user_id=user_id, year=year, dependents_count=count)
        db.add(row)
    else:
        row.dependents_count = count
    db.commit()
    return count


def list_statements(db: Session, user_id: uuid.UUID, year: int) -> list[TaxIncomeStatement]:
    return list(
        db.scalars(
            select(TaxIncomeStatement)
            .where(TaxIncomeStatement.user_id == user_id, TaxIncomeStatement.year == year)
            .order_by(TaxIncomeStatement.kind, TaxIncomeStatement.payer_name)
        )
    )


def add_statement(
    db: Session,
    user_id: uuid.UUID,
    year: int,
    payer_name: str,
    kind: str,
    gross_income: Decimal,
    social_security: Decimal,
    withheld_tax: Decimal,
    note: str | None,
    today: date | None = None,
) -> TaxIncomeStatement:
    _check_year(year, today or date.today())
    if kind not in STATEMENT_KINDS:
        raise InvalidKindError(kind)
    row = TaxIncomeStatement(
        user_id=user_id,
        year=year,
        payer_name=payer_name,
        kind=kind,
        gross_income=gross_income,
        social_security=social_security,
        withheld_tax=withheld_tax,
        note=note,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def delete_statement(db: Session, user_id: uuid.UUID, statement_id: uuid.UUID) -> None:
    row = db.scalar(
        select(TaxIncomeStatement).where(TaxIncomeStatement.id == statement_id, TaxIncomeStatement.user_id == user_id)
    )
    if row is None:
        raise StatementNotFoundError(statement_id)
    db.delete(row)
    db.commit()


# ---------- dossiê ----------

def _totals_by_kind(statements: list[TaxIncomeStatement]) -> dict[str, dict[str, Decimal]]:
    totals = {kind: {"gross": ZERO, "social_security": ZERO, "withheld": ZERO} for kind in STATEMENT_KINDS}
    for s in statements:
        bucket = totals[s.kind]
        bucket["gross"] += s.gross_income
        bucket["social_security"] += s.social_security
        bucket["withheld"] += s.withheld_tax
    return totals


def _tagged_expenses(db: Session, user_id: uuid.UUID, year: int) -> tuple[dict[str, Decimal], int]:
    """Soma das despesas do ano em categorias com marca fiscal; e quantas categorias de despesa não têm marca."""
    kinds = {c.id: c.ir_kind for c in categories_service.list_categories(db, user_id)}
    totals = {"deduction_health": ZERO, "deduction_education": ZERO, "deduction_pension": ZERO}
    used: set[uuid.UUID] = set()
    for t in transactions_service.list_transactions(db, user_id, date(year, 1, 1), date(year, 12, 31)):
        if t.type != TransactionType.EXPENSE:
            continue
        kind = kinds.get(t.category_id)
        if kind in totals:
            totals[kind] += t.amount
        else:
            used.add(t.category_id)
    return totals, len(used)


def dossier(db: Session, user_id: uuid.UUID, year: int, today: date | None = None) -> Dossier:
    """RF-062 a RF-064: tudo o que a declaração do ano pede, com as regras do ano (RF-065)."""
    today = today or date.today()
    _check_year(year, today)
    params = load(year)  # UnsupportedYearError se não houver parâmetros do ano
    as_of = min(date(year, 12, 31), today)

    statements = list_statements(db, user_id, year)
    totals = _totals_by_kind(statements)
    taxable = sum((totals[k]["gross"] for k in TAXABLE_KINDS), ZERO)
    inss = sum((totals[k]["social_security"] for k in TAXABLE_KINDS), ZERO)
    withheld = sum((totals[k]["withheld"] for k in TAXABLE_KINDS), ZERO)

    expenses, untagged = _tagged_expenses(db, user_id, year)
    dependents = get_dependents(db, user_id, year)
    estimate = calc.annual_estimate(
        taxable, inss, withheld,
        expenses["deduction_health"], expenses["deduction_education"], expenses["deduction_pension"],
        dependents, params,
    )

    # Renda variável: histórico inteiro (o prejuízo acumulado vem de meses anteriores), saída só do ano.
    sales = investments_service.list_sales(db, user_id, date(year, 12, 31))
    supported = {"stock": "stock", "fii": "fii"}
    covered = [
        calc.Sale(s.occurred_at, supported[s.asset_class], s.gross, s.gain)
        for s in sales
        if s.asset_class in supported and not s.same_day_buy
    ]
    months = [m for m in calc.variable_income(covered, params) if m.month.startswith(f"{year}-")]
    flags = []
    for s in sales:
        if s.occurred_at.year != year:
            continue
        if s.same_day_buy and s.asset_class in supported:
            flags.append(f"{s.name} em {s.occurred_at:%d/%m/%Y}: compra e venda no mesmo dia (possível day trade, não apurado)")
        elif s.asset_class not in supported:
            flags.append(f"{s.name} em {s.occurred_at:%d/%m/%Y}: classe sem regra verificada (não apurado)")

    # Bens, direitos e dívidas em 31/12 (ou hoje, se o ano não terminou): CUSTO, não mercado (RB-041).
    worth = net_worth_report.net_worth(db, user_id, as_of, today=today)
    rights: list[AssetRight] = [AssetRight("Contas", c.name, c.amount) for c in worth.cash if c.amount != 0]
    for view in investments_service.portfolio(db, user_id, as_of, include_empty=False):
        rights.append(AssetRight("Investimentos", view.asset.name, view.cost, "custo médio × quantidade"))
    for view in assets_service.list_views(db, user_id, as_of):
        if view.value == 0:
            continue
        cost = view.asset.acquisition_value
        rights.append(
            AssetRight(
                "Bens",
                view.asset.name,
                cost if cost is not None else ZERO,
                None if cost is not None else "sem valor de aquisição informado: preencha em Bens",
            )
        )
    debts = [AssetRight("Dívidas", d.name, d.amount) for d in worth.debts]
    debts += [AssetRight("Cartões", c.name, c.amount) for c in worth.cards if c.amount > 0]

    warnings: list[str] = []
    if not statements:
        warnings.append("Nenhum informe de rendimentos cadastrado: o imposto estimado considera rendimento zero.")
    if any(r.note and "sem valor de aquisição" in r.note for r in rights):
        warnings.append("Há bens sem valor de aquisição: o total de bens e direitos está incompleto.")
    if as_of < date(year, 12, 31):
        warnings.append(f"O ano ainda não terminou: bens, direitos e dívidas estão na posição de {as_of:%d/%m/%Y}.")

    return Dossier(
        year=year,
        as_of=as_of,
        parameters=params,
        dependents=dependents,
        statements=statements,
        totals_by_kind=totals,
        estimate=estimate,
        variable_income=months,
        day_trade_flags=flags,
        assets_and_rights=rights,
        debts=debts,
        untagged_expense_categories=untagged,
        warnings=warnings,
    )
