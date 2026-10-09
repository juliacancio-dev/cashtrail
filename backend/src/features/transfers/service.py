import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from src.features.accounts import service as accounts_service
from src.features.transfers import repository
from src.features.transfers.models import Transfer


class TransferNotFoundError(Exception):
    pass


class InvalidAccountError(Exception):
    pass


class ArchivedAccountError(Exception):
    """RB-015: conta arquivada não aceita movimentação nova (reaproveita RB-003)."""


class SameAccountError(Exception):
    """RB-015: origem e destino precisam ser contas diferentes."""


class FutureDateError(Exception):
    """Transferência é um fato já ocorrido; data futura não é aceita."""


def list_transfers(
    db: Session,
    user_id: uuid.UUID,
    start_date: date | None = None,
    end_date: date | None = None,
    account_id: uuid.UUID | None = None,
) -> list[Transfer]:
    return repository.list_by_user(db, user_id, start_date, end_date, account_id)


def get_transfer(db: Session, user_id: uuid.UUID, transfer_id: uuid.UUID) -> Transfer:
    transfer = repository.get_by_id_and_user(db, transfer_id, user_id)
    if transfer is None:
        raise TransferNotFoundError(transfer_id)
    return transfer


def create_transfer(
    db: Session,
    user_id: uuid.UUID,
    from_account_id: uuid.UUID,
    to_account_id: uuid.UUID,
    amount: Decimal,
    occurred_at: date,
    description: str | None,
    commit: bool = True,
    today: date | None = None,
) -> Transfer:
    """RF-023/RB-014/RB-015. Valida posse e estado das duas contas antes de gravar.

    `commit=False` deixa a slice chamadora (ex: pagamento de fatura) gravar o vínculo
    dela na mesma transação.
    """
    if from_account_id == to_account_id:
        raise SameAccountError(from_account_id)

    if occurred_at > (today or date.today()):
        raise FutureDateError(occurred_at)

    for account_id in (from_account_id, to_account_id):
        try:
            account = accounts_service.get_account(db, user_id, account_id)
        except accounts_service.AccountNotFoundError:
            raise InvalidAccountError(account_id)
        if account.is_archived:
            raise ArchivedAccountError(account_id)

    return repository.create(db, user_id, from_account_id, to_account_id, amount, occurred_at, description, commit)


def delete_transfer(db: Session, user_id: uuid.UUID, transfer_id: uuid.UUID, commit: bool = True) -> None:
    transfer = get_transfer(db, user_id, transfer_id)
    repository.delete(db, transfer, commit)


def sum_into_account(db: Session, user_id: uuid.UUID, account_id: uuid.UUID) -> Decimal:
    return repository.sum_into_account(db, user_id, account_id)


def sum_out_of_account(db: Session, user_id: uuid.UUID, account_id: uuid.UUID) -> Decimal:
    return repository.sum_out_of_account(db, user_id, account_id)
