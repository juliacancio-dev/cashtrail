import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.config import settings
from src.core.database import get_db
from src.core.dependencies import CurrentUser
from src.features.investments import service
from src.features.investments.providers import (
    IndexProvider,
    QuoteProvider,
    get_index_provider,
    get_quote_provider,
)
from src.features.investments.schemas import (
    AssetCreate,
    AssetUpdate,
    BenchmarkRead,
    OperationCreate,
    OperationRead,
    Portfolio,
    PortfolioTotals,
    PositionDetail,
    PositionRead,
    QuoteCreate,
    RefreshRead,
)

router = APIRouter(prefix="/investments", tags=["investments"])

ERRORS = {
    service.AssetNotFoundError: (404, "ativo nao encontrado"),
    service.OperationNotFoundError: (404, "operacao nao encontrada"),
    service.InvalidAccountError: (404, "conta nao encontrada ou do tipo errado"),
    service.InvalidCategoryError: (404, "categoria nao encontrada"),
    service.ArchivedAccountError: (422, "conta arquivada nao aceita movimentacao"),
    service.CategoryRequiredError: (422, "informe a categoria do provento ou do ganho/perda"),
    service.InvalidClassError: (422, "classe, fonte ou simbolo invalido"),
    service.InvalidOperationError: (422, "quantidade, preco ou valor invalido"),
    service.PositionInvalidError: (422, "venda acima da quantidade em carteira"),
    service.FutureDateError: (422, "a data nao pode estar no futuro"),
    service.DuplicateSymbolError: (409, "este simbolo ja existe nesta conta"),
    service.ChronologyError: (409, "registre as operacoes em ordem cronologica"),
    service.NotLastOperationError: (409, "so a ultima operacao do ativo pode ser desfeita"),
}
HANDLED = tuple(ERRORS)


def _translate(exc: Exception) -> HTTPException:
    for cls, (code, message) in ERRORS.items():
        if isinstance(exc, cls):
            return HTTPException(code, detail=message)
    raise exc


def _position(view: service.PositionView) -> dict:
    a = view.asset
    return dict(
        id=a.id,
        account_id=a.account_id,
        name=a.name,
        symbol=a.symbol,
        asset_class=a.asset_class,
        quote_source=a.quote_source,
        is_archived=a.is_archived,
        quantity=view.quantity,
        avg_cost=view.avg_cost,
        cost=view.cost,
        price=view.price,
        price_date=view.price_date,
        price_source=view.price_source,
        market_value=view.market_value,
        has_quote=view.has_quote,
        is_stale_quote=view.is_stale_quote,
        unrealized=view.unrealized,
        unrealized_pct=view.unrealized_pct,
        invested=view.invested,
        proceeds=view.proceeds,
        income=view.income,
        realized=view.realized,
        total_return=view.total_return,
        total_return_pct=view.total_return_pct,
        first_buy=view.first_buy,
    )


@router.get("", response_model=Portfolio)
def get_portfolio(current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]) -> Portfolio:
    views = service.portfolio(db, current_user.id)
    active = [v for v in views if not v.asset.is_archived or v.quantity > 0]
    market = sum((v.market_value for v in active), service.ZERO)
    cost = sum((v.cost for v in active), service.ZERO)
    invested = sum((v.invested for v in views), service.ZERO)
    income = sum((v.income for v in views), service.ZERO)
    realized = sum((v.realized for v in views), service.ZERO)
    returned = sum((v.proceeds + v.income for v in views), service.ZERO)
    total_return = market + returned - invested

    warnings: list[str] = []
    if any(v.quantity > 0 and not v.has_quote for v in active):
        warnings.append("Há ativos sem cotação: eles aparecem pelo custo até você atualizar ou informar o valor.")
    if any(v.is_stale_quote for v in active):
        warnings.append("Há cotações com mais de 3 dias úteis; atualize para o valor não ficar defasado.")

    return Portfolio(
        positions=[PositionRead(**_position(v)) for v in active],
        totals=PortfolioTotals(
            market_value=market,
            cost=cost,
            unrealized=market - cost,
            invested=invested,
            income=income,
            realized=realized,
            total_return=total_return,
            total_return_pct=service._pct(total_return, invested),
        ),
        warnings=warnings,
    )


@router.post("/assets", response_model=PositionRead, status_code=status.HTTP_201_CREATED)
def create_asset(
    payload: AssetCreate, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> PositionRead:
    try:
        asset = service.create_asset(db, current_user.id, **payload.model_dump())
        view, _ = service.get_detail(db, current_user.id, asset.id)
    except HANDLED as exc:
        raise _translate(exc)
    return PositionRead(**_position(view))


@router.get("/assets/{asset_id}", response_model=PositionDetail)
def get_asset(
    asset_id: uuid.UUID, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> PositionDetail:
    try:
        view, operations = service.get_detail(db, current_user.id, asset_id)
    except HANDLED as exc:
        raise _translate(exc)
    return PositionDetail(
        **_position(view),
        operations=[OperationRead.model_validate(op) for op in reversed(operations)],
    )


@router.patch("/assets/{asset_id}", response_model=PositionRead)
def update_asset(
    asset_id: uuid.UUID,
    payload: AssetUpdate,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> PositionRead:
    try:
        service.update_asset(db, current_user.id, asset_id, payload.model_dump(exclude_unset=True))
        view, _ = service.get_detail(db, current_user.id, asset_id)
    except HANDLED as exc:
        raise _translate(exc)
    return PositionRead(**_position(view))


@router.post(
    "/assets/{asset_id}/operations", response_model=PositionDetail, status_code=status.HTTP_201_CREATED
)
def add_operation(
    asset_id: uuid.UUID,
    payload: OperationCreate,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> PositionDetail:
    try:
        service.add_operation(db, current_user.id, asset_id, **payload.model_dump())
        view, operations = service.get_detail(db, current_user.id, asset_id)
    except HANDLED as exc:
        raise _translate(exc)
    return PositionDetail(
        **_position(view), operations=[OperationRead.model_validate(op) for op in reversed(operations)]
    )


@router.delete("/assets/{asset_id}/operations/{operation_id}", response_model=PositionDetail)
def undo_operation(
    asset_id: uuid.UUID,
    operation_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> PositionDetail:
    try:
        service.undo_operation(db, current_user.id, asset_id, operation_id)
        view, operations = service.get_detail(db, current_user.id, asset_id)
    except HANDLED as exc:
        raise _translate(exc)
    return PositionDetail(
        **_position(view), operations=[OperationRead.model_validate(op) for op in reversed(operations)]
    )


@router.post("/assets/{asset_id}/quote", response_model=PositionDetail, status_code=status.HTTP_201_CREATED)
def set_quote(
    asset_id: uuid.UUID,
    payload: QuoteCreate,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> PositionDetail:
    try:
        service.set_manual_quote(db, current_user.id, asset_id, payload.price, payload.quoted_on)
        view, operations = service.get_detail(db, current_user.id, asset_id)
    except HANDLED as exc:
        raise _translate(exc)
    return PositionDetail(
        **_position(view), operations=[OperationRead.model_validate(op) for op in reversed(operations)]
    )


@router.post("/refresh", response_model=RefreshRead)
def refresh(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    provider: Annotated[QuoteProvider, Depends(get_quote_provider)],
) -> RefreshRead:
    result = service.refresh_quotes(db, current_user.id, provider, monthly_cap=settings.quotes_monthly_cap)
    return RefreshRead(**result.__dict__)


@router.get("/benchmark", response_model=BenchmarkRead)
def get_benchmark(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    index_provider: Annotated[IndexProvider, Depends(get_index_provider)],
) -> BenchmarkRead:
    return BenchmarkRead(**service.benchmark(db, current_user.id, index_provider).__dict__)
