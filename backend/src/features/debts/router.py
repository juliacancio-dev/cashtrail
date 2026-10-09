import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.dependencies import CurrentUser
from src.features.debts import service
from src.features.debts.schemas import (
    AmortizationCreate,
    AmortizationPreview,
    AmortizationPreviewRequest,
    AmortizationRead,
    DebtCreate,
    DebtDetail,
    DebtRead,
    DebtsSummary,
    InstallmentPay,
    InstallmentRead,
    InstallmentUpdate,
    NextInstallment,
    PlannedInstallmentRead,
    ScheduleParams,
    SchedulePreview,
)

router = APIRouter(prefix="/debts", tags=["debts"])

NOT_FOUND = {
    service.DebtNotFoundError: "divida nao encontrada",
    service.InstallmentNotFoundError: "parcela nao encontrada",
    service.InvalidAccountError: "conta nao encontrada",
    service.InvalidCategoryError: "categoria nao encontrada",
}

UNPROCESSABLE = {
    service.ArchivedAccountError: "conta arquivada nao aceita movimentacao",
    service.InvalidScheduleError: "parametros nao geram um cronograma valido",
    service.InvalidAmountError: "valor invalido: acima do saldo devedor ou da parcela abaixo do principal",
    service.FutureDateError: "a data nao pode estar no futuro",
    service.AccountRequiredError: "informe a conta de origem do pagamento",
}

CONFLICT = {
    service.InstallmentLockedError: "parcela ja paga, cancelada ou substituida por um recalculo",
    service.DebtPaidOffError: "divida ja quitada",
    service.NoPaymentError: "a parcela nao tem pagamento para desfazer",
}


def _translate(exc: Exception) -> HTTPException:
    for table, code in ((NOT_FOUND, 404), (UNPROCESSABLE, 422), (CONFLICT, 409)):
        for cls, message in table.items():
            if isinstance(exc, cls):
                return HTTPException(code, detail=message)
    raise exc


HANDLED = tuple([*NOT_FOUND, *UNPROCESSABLE, *CONFLICT])


def _planned(row: service.PlannedInstallment) -> PlannedInstallmentRead:
    return PlannedInstallmentRead(**row.__dict__)


def _installment(item: service.InstallmentView) -> InstallmentRead:
    return InstallmentRead(
        id=item.installment.id,
        number=item.installment.number,
        commitment_id=item.commitment.id,
        due_date=item.commitment.due_date,
        amount=item.amount,
        principal_part=item.installment.principal_part,
        charges=item.charges,
        status=item.status,
        paid=item.status == "paid",
    )


def _read(view: service.DebtView) -> dict:
    d = view.debt
    nxt = view.next_installment
    return dict(
        id=d.id,
        account_id=d.account_id,
        name=view.account.name,
        creditor=d.creditor,
        principal=d.principal,
        contracted_at=d.contracted_at,
        installments=d.installments,
        system=d.system,
        monthly_rate=d.monthly_rate,
        first_due_date=d.first_due_date,
        payment_account_id=d.payment_account_id,
        interest_category_id=d.interest_category_id,
        outstanding=view.outstanding,
        principal_paid=view.principal_paid,
        charges_paid=view.charges_paid,
        charges_projected=view.charges_projected,
        installments_paid=view.installments_paid,
        installments_open=view.installments_open,
        next_installment=NextInstallment(
            id=nxt.installment.id,
            number=nxt.installment.number,
            due_date=nxt.commitment.due_date,
            amount=nxt.amount,
            status=nxt.status,
        )
        if nxt
        else None,
        is_paid_off=view.is_paid_off,
    )


def _detail(detail: service.DebtDetail) -> DebtDetail:
    return DebtDetail(
        **_read(detail.view),
        installment_list=[_installment(i) for i in detail.installments if i.status != "superseded"],
        amortizations=[AmortizationRead.model_validate(a) for a in detail.amortizations],
        settlement_ids=detail.settlements,
    )


@router.get("", response_model=list[DebtRead])
def list_debts(current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]) -> list[DebtRead]:
    return [DebtRead(**_read(v)) for v in service.list_debts(db, current_user.id)]


@router.get("/summary", response_model=DebtsSummary)
def debts_summary(current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]) -> DebtsSummary:
    return DebtsSummary(**service.summary(db, current_user.id))


@router.post("/preview", response_model=SchedulePreview)
def preview(payload: ScheduleParams, current_user: CurrentUser) -> SchedulePreview:
    try:
        rows = service.preview_schedule(
            payload.principal, payload.installments, payload.first_due_date, payload.system, payload.monthly_rate
        )
    except service.InvalidScheduleError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail=UNPROCESSABLE[service.InvalidScheduleError])
    total = sum((r.amount for r in rows), service.ZERO)
    return SchedulePreview(
        rows=[_planned(r) for r in rows], total_paid=total, total_charges=total - payload.principal
    )


@router.post("", response_model=DebtDetail, status_code=status.HTTP_201_CREATED)
def create_debt(
    payload: DebtCreate, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> DebtDetail:
    try:
        view = service.create_debt(db, current_user.id, **payload.model_dump())
        return _detail(service.get_debt(db, current_user.id, view.debt.id))
    except HANDLED as exc:
        raise _translate(exc)


@router.get("/{debt_id}", response_model=DebtDetail)
def get_debt(debt_id: uuid.UUID, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]) -> DebtDetail:
    try:
        return _detail(service.get_debt(db, current_user.id, debt_id))
    except HANDLED as exc:
        raise _translate(exc)


@router.patch("/{debt_id}/installments/{installment_id}", response_model=InstallmentRead)
def update_installment(
    debt_id: uuid.UUID,
    installment_id: uuid.UUID,
    payload: InstallmentUpdate,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> InstallmentRead:
    try:
        item = service.update_installment(
            db, current_user.id, debt_id, installment_id, payload.model_dump(exclude_unset=True, exclude_none=True)
        )
    except HANDLED as exc:
        raise _translate(exc)
    return _installment(item)


@router.post("/{debt_id}/installments/{installment_id}/payment", response_model=InstallmentRead)
def pay_installment(
    debt_id: uuid.UUID,
    installment_id: uuid.UUID,
    payload: InstallmentPay,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> InstallmentRead:
    try:
        item = service.pay_installment(
            db, current_user.id, debt_id, installment_id, payload.paid_at, payload.account_id
        )
    except HANDLED as exc:
        raise _translate(exc)
    return _installment(item)


@router.delete("/{debt_id}/installments/{installment_id}/payment", response_model=InstallmentRead)
def undo_payment(
    debt_id: uuid.UUID,
    installment_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> InstallmentRead:
    try:
        item = service.undo_payment(db, current_user.id, debt_id, installment_id)
    except HANDLED as exc:
        raise _translate(exc)
    return _installment(item)


@router.post("/{debt_id}/amortization-preview", response_model=AmortizationPreview)
def amortization_preview(
    debt_id: uuid.UUID,
    payload: AmortizationPreviewRequest,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> AmortizationPreview:
    try:
        plan = service.preview_amortization(db, current_user.id, debt_id, payload.amount, payload.mode)
    except HANDLED as exc:
        raise _translate(exc)
    return AmortizationPreview(
        outstanding_before=plan.outstanding_before,
        outstanding_after=plan.outstanding_after,
        installments_before=plan.installments_before,
        installments_after=len(plan.rows),
        charges_before=plan.charges_before,
        charges_after=plan.charges_after,
        rows=[_planned(r) for r in plan.rows],
    )


@router.post("/{debt_id}/amortizations", response_model=DebtDetail, status_code=status.HTTP_201_CREATED)
def amortize(
    debt_id: uuid.UUID,
    payload: AmortizationCreate,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> DebtDetail:
    try:
        detail = service.amortize(
            db, current_user.id, debt_id, payload.amount, payload.mode, payload.paid_at, payload.account_id
        )
    except HANDLED as exc:
        raise _translate(exc)
    return _detail(detail)
