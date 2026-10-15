import csv
import io
import uuid
from dataclasses import asdict
from datetime import date
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.dependencies import CurrentUser
from src.features.reports.csv_export import BOM, number, safe_text
from src.features.tax import service
from src.features.tax.schemas import (
    DependentsUpdate,
    DossierRead,
    EstimateRead,
    KindTotals,
    MonthRead,
    ParametersRead,
    RightRead,
    SourceRead,
    StatementCreate,
    StatementRead,
    YearsRead,
)

router = APIRouter(prefix="/tax", tags=["tax"])

DISCLAIMER = (
    "Estimativa para organizar a declaração. O CashTrail não é o programa da Receita, não transmite a "
    "declaração e não substitui um contador: confira tudo no programa oficial."
)


def _dossier_read(d: service.Dossier) -> DossierRead:
    p = d.parameters
    return DossierRead(
        year=d.year,
        as_of=d.as_of,
        disclaimer=DISCLAIMER,
        parameters=ParametersRead(
            year=p.year,
            label=p.label,
            consulted_at=p.consulted_at,
            sources=[SourceRead(**s) for s in p.sources],
            unverified=p.unverified,
            dependent_deduction=p.dependent_deduction,
            education_limit_per_person=p.education_limit_per_person,
            simplified_limit=p.simplified_limit,
            stock_exempt_monthly_sales=p.variable_income.stock_exempt_monthly_sales,
            darf_code=p.variable_income.darf_code,
        ),
        dependents=d.dependents,
        statements=[StatementRead.model_validate(s) for s in d.statements],
        totals_by_kind={k: KindTotals(**v) for k, v in d.totals_by_kind.items()},
        estimate=EstimateRead(**asdict(d.estimate)),
        variable_income=[MonthRead(**asdict(m)) for m in d.variable_income],
        day_trade_flags=d.day_trade_flags,
        assets_and_rights=[RightRead(**asdict(r)) for r in d.assets_and_rights],
        debts=[RightRead(**asdict(r)) for r in d.debts],
        untagged_expense_categories=d.untagged_expense_categories,
        warnings=d.warnings,
    )


def _load(db: Session, user_id: uuid.UUID, year: int) -> service.Dossier:
    try:
        return service.dossier(db, user_id, year)
    except service.InvalidYearError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail="ano invalido")
    except service.UnsupportedYearError:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="ainda nao ha parametros fiscais verificados para este ano",
        )


@router.get("/years", response_model=YearsRead)
def get_years(current_user: CurrentUser) -> YearsRead:
    years = service.available_years()
    return YearsRead(years=years, default_year=max(years) if years else date.today().year)


@router.get("/{year}", response_model=DossierRead)
def get_dossier(year: int, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]) -> DossierRead:
    return _dossier_read(_load(db, current_user.id, year))


@router.put("/{year}/dependents", response_model=DossierRead)
def put_dependents(
    year: int, payload: DependentsUpdate, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> DossierRead:
    try:
        service.set_dependents(db, current_user.id, year, payload.count)
    except service.InvalidYearError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail="ano invalido")
    return _dossier_read(_load(db, current_user.id, year))


@router.post("/{year}/statements", response_model=DossierRead, status_code=status.HTTP_201_CREATED)
def add_statement(
    year: int, payload: StatementCreate, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> DossierRead:
    try:
        service.add_statement(db, current_user.id, year, **payload.model_dump())
    except service.InvalidYearError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail="ano invalido")
    except service.InvalidKindError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail="tipo de rendimento invalido")
    return _dossier_read(_load(db, current_user.id, year))


@router.delete("/{year}/statements/{statement_id}", response_model=DossierRead)
def delete_statement(
    year: int, statement_id: uuid.UUID, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> DossierRead:
    try:
        service.delete_statement(db, current_user.id, statement_id)
    except service.StatementNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="informe nao encontrado")
    return _dossier_read(_load(db, current_user.id, year))


KIND_LABELS = {
    "salary": "Salário (tributável)",
    "other_taxable": "Outro rendimento tributável",
    "thirteenth": "13º salário (exclusivo na fonte)",
    "plr": "PLR (exclusivo na fonte)",
    "exclusive_other": "Rendimento financeiro (exclusivo na fonte)",
    "exempt": "Rendimento isento",
}


def _csv(d: service.Dossier) -> str:
    def m(value: Decimal | None) -> str:
        return number(value)

    rows: list[list[str]] = [
        [safe_text(f"Dossiê IRPF {d.year} (posição em {d.as_of:%d/%m/%Y})")],
        [safe_text(DISCLAIMER)],
        [safe_text(d.parameters.label), safe_text(f"parâmetros consultados em {d.parameters.consulted_at:%d/%m/%Y}")],
        [],
        ["Rendimentos", "Fonte pagadora", "Bruto", "INSS", "IRRF"],
    ]
    for s in d.statements:
        rows.append([safe_text(KIND_LABELS[s.kind]), safe_text(s.payer_name), m(s.gross_income), m(s.social_security), m(s.withheld_tax)])
    e = d.estimate
    rows += [
        [],
        ["Estimativa", "Completa", "Simplificada"],
        ["Rendimentos tributáveis", m(e.taxable_income), m(e.taxable_income)],
        ["Deduções", m(e.complete.deductions), m(e.simplified.deductions)],
        ["Base de cálculo", m(e.complete.base), m(e.simplified.base)],
        ["Imposto antes do redutor", m(e.complete.tax_before_reducer), m(e.simplified.tax_before_reducer)],
        ["Redutor (Lei 15.270/2025)", m(e.complete.reducer), m(e.simplified.reducer)],
        ["Imposto devido", m(e.complete.tax_due), m(e.simplified.tax_due)],
        ["IRRF já retido", m(e.withheld_tax), m(e.withheld_tax)],
        ["Saldo (positivo a pagar, negativo a restituir)", m(e.complete.balance), m(e.simplified.balance)],
        ["Mais vantajosa", safe_text(e.best), ""],
        [],
        ["Renda variável", "Mês", "Vendas", "Ganho", "Prejuízo usado", "Imposto", "IRRF", "DARF", "Vencimento"],
    ]
    for month in d.variable_income:
        rows.append(
            [
                "ações" if month.modality == "stock" else "FII",
                month.month,
                m(month.sales),
                m(month.gain),
                m(month.loss_used),
                m(month.tax),
                m(month.irrf),
                m(month.darf_amount),
                f"{month.due_date:%d/%m/%Y}",
            ]
        )
    rows += [[], ["Bens e direitos (custo)", "Item", "Valor"]]
    for r in d.assets_and_rights:
        rows.append([safe_text(r.group), safe_text(r.name), m(r.amount)])
    rows += [[], ["Dívidas", "Item", "Valor"]]
    for r in d.debts:
        rows.append([safe_text(r.group), safe_text(r.name), m(r.amount)])

    buffer = io.StringIO()
    csv.writer(buffer, delimiter=";", lineterminator="\r\n").writerows(rows)
    return BOM + buffer.getvalue()


@router.get("/{year}/export.csv")
def export_csv(year: int, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]) -> Response:
    d = _load(db, current_user.id, year)
    return Response(
        content=_csv(d),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="irpf-{year}.csv"'},
    )
