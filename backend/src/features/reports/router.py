from dataclasses import asdict
from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.dependencies import CurrentUser
from src.features.reports import balances_dre, cash_flow, csv_export
from src.features.reports.schemas import (
    BalancesRead,
    CashFlowRead,
    DreRead,
    FlowItemRead,
)

router = APIRouter(prefix="/reports", tags=["reports"])

MAX_DRE_DAYS = 366 * 5


def _period(start_date: date | None, end_date: date | None) -> tuple[date, date]:
    start = start_date or date.today().replace(day=1)
    end = end_date or cash_flow.last_of_month(start.replace(day=1))
    if end < start:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail="a data final nao pode ser anterior a inicial")
    if (end - start).days > MAX_DRE_DAYS:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail="periodo maior que 5 anos")
    return start, end


def _month(value: str | None, default: date) -> date:
    if value is None:
        return default
    try:
        return cash_flow.parse_month(value)
    except (ValueError, TypeError):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail="mes invalido, use AAAA-MM")


def _default_start_month() -> date:
    """Padrão: o mês passado (para ver o realizado) até 4 meses à frente com 6 meses."""
    return cash_flow.add_months(date.today().replace(day=1), -1)


def _csv_response(content: str, filename: str) -> Response:
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/balances", response_model=BalancesRead)
def get_balances(current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]) -> BalancesRead:
    result = balances_dre.balances(db, current_user.id)
    return BalancesRead(**asdict(result))


@router.get("/dre", response_model=DreRead)
def get_dre(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    include_forecast: bool = Query(default=False),
) -> DreRead:
    start, end = _period(start_date, end_date)
    return DreRead(**asdict(balances_dre.dre(db, current_user.id, start, end, include_forecast)))


@router.get("/dre.csv")
def get_dre_csv(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    include_forecast: bool = Query(default=False),
) -> Response:
    start, end = _period(start_date, end_date)
    result = balances_dre.dre(db, current_user.id, start, end, include_forecast)
    return _csv_response(csv_export.dre_csv(result), f"dre-{start:%Y%m%d}-{end:%Y%m%d}.csv")


@router.get("/cash-flow", response_model=CashFlowRead)
def get_cash_flow(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    start_month: str | None = Query(default=None, description="AAAA-MM"),
    months: int = Query(default=6, ge=1, le=cash_flow.MAX_MONTHS),
) -> CashFlowRead:
    flow = cash_flow.build_cash_flow(db, current_user.id, _month(start_month, _default_start_month()), months)
    return CashFlowRead(**asdict(flow))


@router.get("/cash-flow.csv")
def get_cash_flow_csv(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    start_month: str | None = Query(default=None, description="AAAA-MM"),
    months: int = Query(default=6, ge=1, le=cash_flow.MAX_MONTHS),
) -> Response:
    flow = cash_flow.build_cash_flow(db, current_user.id, _month(start_month, _default_start_month()), months)
    return _csv_response(csv_export.cash_flow_csv(flow), f"fluxo-de-caixa-{flow.start_month}.csv")


@router.get("/cash-flow/items", response_model=list[FlowItemRead])
def get_cash_flow_items(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    month: str = Query(description="AAAA-MM"),
    column: Literal["planned", "realized", "projected"] = Query(),
    direction: Literal["in", "out"] = Query(),
) -> list[FlowItemRead]:
    items = cash_flow.month_items(db, current_user.id, _month(month, date.today().replace(day=1)), column, direction)
    return [
        FlowItemRead(
            column=i.column,
            direction=i.direction,
            when=i.when,
            amount=i.amount,
            source=i.source,
            description=i.description,
            category_id=i.category_id,
            category_name=i.category_name,
        )
        for i in items
    ]
