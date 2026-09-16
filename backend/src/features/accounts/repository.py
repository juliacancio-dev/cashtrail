import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.features.accounts.models import Account, AccountType


def list_by_user(db: Session, user_id: uuid.UUID) -> list[Account]:
    return list(db.scalars(select(Account).where(Account.user_id == user_id).order_by(Account.created_at)))


def get_by_id_and_user(db: Session, account_id: uuid.UUID, user_id: uuid.UUID) -> Account | None:
    """RNF-001: toda leitura já nasce filtrada por user_id, nunca só por id."""
    return db.scalar(
        select(Account).where(Account.id == account_id, Account.user_id == user_id)
    )


def create(db: Session, user_id: uuid.UUID, name: str, type: AccountType) -> Account:
    account = Account(user_id=user_id, name=name, type=type)
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def rename(db: Session, account: Account, name: str) -> Account:
    account.name = name
    db.commit()
    db.refresh(account)
    return account


def archive(db: Session, account: Account) -> Account:
    account.is_archived = True
    db.commit()
    db.refresh(account)
    return account
