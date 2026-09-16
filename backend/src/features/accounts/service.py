import uuid

from sqlalchemy.orm import Session

from src.features.accounts import repository
from src.features.accounts.models import Account, AccountType


class AccountNotFoundError(Exception):
    pass


def list_accounts(db: Session, user_id: uuid.UUID) -> list[Account]:
    return repository.list_by_user(db, user_id)


def create_account(db: Session, user_id: uuid.UUID, name: str, type: AccountType) -> Account:
    return repository.create(db, user_id=user_id, name=name, type=type)


def get_account(db: Session, user_id: uuid.UUID, account_id: uuid.UUID) -> Account:
    account = repository.get_by_id_and_user(db, account_id, user_id)
    if account is None:
        raise AccountNotFoundError(account_id)

    return account


def rename_account(db: Session, user_id: uuid.UUID, account_id: uuid.UUID, name: str) -> Account:
    account = get_account(db, user_id, account_id)
    return repository.rename(db, account, name)


def archive_account(db: Session, user_id: uuid.UUID, account_id: uuid.UUID) -> Account:
    account = get_account(db, user_id, account_id)
    return repository.archive(db, account)
