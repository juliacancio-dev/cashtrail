import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.dependencies import CurrentUser
from src.features.credit_cards import service
from src.features.credit_cards.schemas import (
    CardCreate,
    CardRead,
    CardsSummary,
    CardUpdate,
    InvoiceDetail,
    InvoiceRead,
    PaymentCreate,
    PaymentRead,
    PurchaseCreate,
    PurchaseMove,
    PurchaseRead,
)

router = APIRouter(prefix="/cards", tags=["cards"])

NOT_FOUND = {
    service.CardNotFoundError: "cartao nao encontrado",
    service.PaymentNotFoundError: "pagamento nao encontrado",
    service.PurchaseNotFoundError: "compra nao encontrada",
    service.InvalidAccountError: "conta nao encontrada",
    service.InvalidCategoryError: "categoria nao encontrada",
}

UNPROCESSABLE = {
    service.ArchivedAccountError: "conta arquivada nao aceita movimentacao",
    service.NotCreditCardAccountError: "a conta precisa ser do tipo cartao de credito",
    service.InvalidInvoiceError: "a data informada nao e um fechamento valido deste cartao",
    service.InvalidAmountError: "valor do pagamento maior que o saldo da fatura",
    service.AccountRequiredError: "informe a conta de origem do pagamento",
    service.SameAccountError: "a conta de origem nao pode ser a propria conta do cartao",
    service.FutureDateError: "a data nao pode estar no futuro",
    service.InvalidInstallmentsError: "numero de parcelas invalido",
}

CONFLICT = {
    service.CardAlreadyExistsError: "esta conta ja tem um cartao configurado",
    service.InvoiceAlreadyPaidError: "esta fatura ja esta quitada",
}


def _http_error(exc: Exception) -> HTTPException:
    for mapping, code in ((NOT_FOUND, 404), (UNPROCESSABLE, 422), (CONFLICT, 409)):
        for error_type, message in mapping.items():
            if isinstance(exc, error_type):
                return HTTPException(code, detail=message)
    raise exc


HANDLED = tuple([*NOT_FOUND, *UNPROCESSABLE, *CONFLICT])


def _card_read(view: service.CardView) -> CardRead:
    c = view.card
    return CardRead(
        id=c.id,
        account_id=c.account_id,
        account_name=view.account_name,
        closing_day=c.closing_day,
        due_day=c.due_day,
        credit_limit=c.credit_limit,
        default_payment_account_id=c.default_payment_account_id,
        debt=view.debt,
        available=view.available,
        over_limit=view.available is not None and view.available < 0,
        created_at=c.created_at,
    )


def _purchase_read(entry: service.InvoiceEntry) -> PurchaseRead:
    t = entry.transaction
    return PurchaseRead(
        transaction_id=t.id,
        description=t.description,
        amount=t.amount,
        type=t.type.value,
        occurred_at=t.occurred_at,
        category_id=t.category_id,
        invoice_closing_date=entry.invoice_closing_date,
        moved=entry.moved,
    )


def _invoice_read(invoice: service.Invoice) -> InvoiceRead:
    return InvoiceRead(
        closing_date=invoice.closing_date,
        period_start=invoice.period_start,
        due_date=invoice.due_date,
        status=invoice.status,
        total=invoice.total,
        paid=invoice.paid,
        balance=invoice.balance,
        previous_closing_date=invoice.previous_closing_date,
        next_closing_date=invoice.next_closing_date,
        purchases_count=len(invoice.entries),
    )


def _invoice_detail(invoice: service.Invoice) -> InvoiceDetail:
    return InvoiceDetail(
        **_invoice_read(invoice).model_dump(),
        purchases=[_purchase_read(e) for e in invoice.entries],
        payments=[
            PaymentRead(id=p.id, transfer_id=p.transfer_id, amount=p.amount, paid_at=p.paid_at, created_at=p.created_at)
            for p in invoice.payments
        ],
    )


@router.get("", response_model=list[CardRead])
def list_cards(current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]) -> list[CardRead]:
    return [_card_read(v) for v in service.list_cards(db, current_user.id)]


@router.get("/summary", response_model=CardsSummary)
def cards_summary(current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]) -> CardsSummary:
    return CardsSummary(**service.summary(db, current_user.id))


@router.post("", response_model=CardRead, status_code=status.HTTP_201_CREATED)
def create_card(
    payload: CardCreate, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> CardRead:
    try:
        view = service.create_card(db, current_user.id, **payload.model_dump())
    except HANDLED as exc:
        raise _http_error(exc)
    return _card_read(view)


@router.get("/{card_id}", response_model=CardRead)
def get_card(card_id: uuid.UUID, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]) -> CardRead:
    try:
        return _card_read(service.get_card(db, current_user.id, card_id))
    except HANDLED as exc:
        raise _http_error(exc)


@router.patch("/{card_id}", response_model=CardRead)
def update_card(
    card_id: uuid.UUID, payload: CardUpdate, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> CardRead:
    try:
        view = service.update_card(db, current_user.id, card_id, payload.model_dump(exclude_unset=True))
    except HANDLED as exc:
        raise _http_error(exc)
    return _card_read(view)


@router.post("/{card_id}/purchases", response_model=list[PurchaseRead], status_code=status.HTTP_201_CREATED)
def create_purchase(
    card_id: uuid.UUID, payload: PurchaseCreate, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> list[PurchaseRead]:
    try:
        entries = service.create_purchase(db, current_user.id, card_id, **payload.model_dump())
    except HANDLED as exc:
        raise _http_error(exc)
    return [_purchase_read(e) for e in entries]


@router.patch("/{card_id}/purchases/{transaction_id}", response_model=PurchaseRead)
def move_purchase(
    card_id: uuid.UUID,
    transaction_id: uuid.UUID,
    payload: PurchaseMove,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> PurchaseRead:
    try:
        entry = service.move_purchase(db, current_user.id, card_id, transaction_id, payload.invoice_closing_date)
    except HANDLED as exc:
        raise _http_error(exc)
    return _purchase_read(entry)


@router.get("/{card_id}/invoices", response_model=list[InvoiceRead])
def list_invoices(
    card_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    limit: int = Query(default=36, ge=1, le=120),
) -> list[InvoiceRead]:
    try:
        invoices = service.list_invoices(db, current_user.id, card_id, limit=limit)
    except HANDLED as exc:
        raise _http_error(exc)
    return [_invoice_read(i) for i in invoices]


@router.get("/{card_id}/invoices/{closing_date}", response_model=InvoiceDetail)
def get_invoice(
    card_id: uuid.UUID, closing_date: date, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> InvoiceDetail:
    try:
        invoice = service.get_invoice(db, current_user.id, card_id, closing_date)
    except HANDLED as exc:
        raise _http_error(exc)
    return _invoice_detail(invoice)


@router.post(
    "/{card_id}/invoices/{closing_date}/payments", response_model=InvoiceDetail, status_code=status.HTTP_201_CREATED
)
def pay_invoice(
    card_id: uuid.UUID,
    closing_date: date,
    payload: PaymentCreate,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> InvoiceDetail:
    try:
        service.pay_invoice(db, current_user.id, card_id, closing_date, **payload.model_dump())
        invoice = service.get_invoice(db, current_user.id, card_id, closing_date)
    except HANDLED as exc:
        raise _http_error(exc)
    return _invoice_detail(invoice)


@router.delete("/{card_id}/invoices/{closing_date}/payments/{payment_id}", response_model=InvoiceDetail)
def undo_payment(
    card_id: uuid.UUID,
    closing_date: date,
    payment_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> InvoiceDetail:
    try:
        service.undo_payment(db, current_user.id, card_id, closing_date, payment_id)
        invoice = service.get_invoice(db, current_user.id, card_id, closing_date)
    except HANDLED as exc:
        raise _http_error(exc)
    return _invoice_detail(invoice)
