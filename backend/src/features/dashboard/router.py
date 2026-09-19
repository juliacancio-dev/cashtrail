from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.dependencies import CurrentUser
from src.features.dashboard import service
from src.features.dashboard.schemas import BalancePoint, CategorySpending, DashboardRead, DashboardSummary

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardRead)
def get_dashboard(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
) -> DashboardRead:
    if start_date is None or end_date is None:
        default_start, default_end = service.default_period()
        start_date = start_date or default_start
        end_date = end_date or default_end

    data = service.build_dashboard(db, current_user.id, start_date, end_date)

    return DashboardRead(
        start_date=start_date,
        end_date=end_date,
        summary=DashboardSummary(
            income_total=data["income_total"],
            expense_total=data["expense_total"],
            balance=data["balance"],
        ),
        by_category=[
            CategorySpending(category_id=cid, category_name=name, total=total)
            for cid, name, total in data["by_category"]
        ],
        balance_evolution=[
            BalancePoint(date=d, balance=balance) for d, balance in data["balance_evolution"]
        ],
    )
