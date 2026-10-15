from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.dependencies import CurrentUser
from src.features.investments.providers import IndexProvider, get_index_provider
from src.features.retirement import service
from src.features.retirement.schemas import OverviewRead, PlanRead, PlanWrite, ResultRead

router = APIRouter(prefix="/retirement", tags=["retirement"])

DISCLAIMER = (
    "Simulação com as premissas que você informou, em valores de hoje. Não é previsão nem recomendação "
    "de investimento; o INSS não é calculado."
)


def _overview(o: service.Overview) -> OverviewRead:
    return OverviewRead(
        disclaimer=DISCLAIMER,
        plan=PlanRead.model_validate(o.plan) if o.plan else None,
        invested_wealth=o.invested_wealth,
        assets_wealth=o.assets_wealth,
        counted_wealth=o.counted_wealth,
        result=ResultRead(**asdict(o.result)) if o.result else None,
        ipca_12m_pct=o.ipca_12m_pct,
        defaults=service.DEFAULTS,
        warnings=o.warnings,
    )


@router.get("", response_model=OverviewRead)
def get_overview(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    index_provider: Annotated[IndexProvider, Depends(get_index_provider)],
) -> OverviewRead:
    return _overview(service.overview(db, current_user.id, index_provider))


@router.put("", response_model=OverviewRead, status_code=status.HTTP_200_OK)
def put_plan(
    payload: PlanWrite,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    index_provider: Annotated[IndexProvider, Depends(get_index_provider)],
) -> OverviewRead:
    try:
        service.save_plan(db, current_user.id, **payload.model_dump())
    except service.InvalidPlanError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail="a idade-alvo precisa ser maior que a atual")
    return _overview(service.overview(db, current_user.id, index_provider))
