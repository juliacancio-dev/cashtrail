import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.features.credit_cards.models import CardInvoicePayment, CardPurchase, CreditCard


def list_cards(db: Session, user_id: uuid.UUID) -> list[CreditCard]:
    return list(db.scalars(select(CreditCard).where(CreditCard.user_id == user_id).order_by(CreditCard.created_at)))


def get_card(db: Session, card_id: uuid.UUID, user_id: uuid.UUID) -> CreditCard | None:
    """RNF-001: toda leitura já nasce filtrada por user_id, nunca só por id."""
    return db.scalar(select(CreditCard).where(CreditCard.id == card_id, CreditCard.user_id == user_id))


def get_card_by_account(db: Session, account_id: uuid.UUID, user_id: uuid.UUID) -> CreditCard | None:
    return db.scalar(select(CreditCard).where(CreditCard.account_id == account_id, CreditCard.user_id == user_id))


def links_by_card(db: Session, card_id: uuid.UUID) -> dict[uuid.UUID, date]:
    rows = db.execute(
        select(CardPurchase.transaction_id, CardPurchase.invoice_closing_date).where(
            CardPurchase.credit_card_id == card_id
        )
    )
    return {transaction_id: closing for transaction_id, closing in rows}


def get_link(db: Session, transaction_id: uuid.UUID) -> CardPurchase | None:
    return db.get(CardPurchase, transaction_id)


def list_payments(db: Session, card_id: uuid.UUID, user_id: uuid.UUID) -> list[CardInvoicePayment]:
    return list(
        db.scalars(
            select(CardInvoicePayment)
            .where(CardInvoicePayment.credit_card_id == card_id, CardInvoicePayment.user_id == user_id)
            .order_by(CardInvoicePayment.paid_at, CardInvoicePayment.created_at)
        )
    )


def get_payment(
    db: Session, payment_id: uuid.UUID, card_id: uuid.UUID, user_id: uuid.UUID
) -> CardInvoicePayment | None:
    return db.scalar(
        select(CardInvoicePayment).where(
            CardInvoicePayment.id == payment_id,
            CardInvoicePayment.credit_card_id == card_id,
            CardInvoicePayment.user_id == user_id,
        )
    )


def add(db: Session, instance: object) -> None:
    """Só adiciona à sessão e faz flush: o commit é do service, junto com o resto."""
    db.add(instance)
    db.flush()


def delete(db: Session, instance: object) -> None:
    # flush imediato: o pagamento precisa sumir ANTES da transferência (FK RESTRICT).
    db.delete(instance)
    db.flush()
