import hashlib
import uuid
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from src.features.accounts import service as accounts_service
from src.features.statement_import import parser, repository
from src.features.statement_import.models import StatementImport
from src.features.statement_import.parser import ColumnMapping, ParseResult
from src.features.transactions import service as transactions_service
from src.features.transactions.models import Transaction, TransactionSource, TransactionType

# RB-006 (04-usecases.md): janela da heurística de duplicata. O banco às vezes
# compensa em D+1/D+2, então a data não precisa ser idêntica; o valor sim.
DUPLICATE_WINDOW_DAYS = 2


class AccountNotFoundError(Exception):
    pass


class ArchivedAccountError(Exception):
    pass


@dataclass
class PreviewResult:
    file_sha256: str
    parsed: ParseResult
    # row_number -> lançamento existente que provavelmente é o mesmo
    duplicates: dict[int, Transaction]
    previously_imported_at: datetime | None


def _check_account(db: Session, user_id: uuid.UUID, account_id: uuid.UUID) -> None:
    try:
        account = accounts_service.get_account(db, user_id, account_id)
    except accounts_service.AccountNotFoundError:
        raise AccountNotFoundError(account_id)
    if account.is_archived:
        raise ArchivedAccountError(account_id)


def find_duplicates(
    db: Session, user_id: uuid.UUID, account_id: uuid.UUID, rows: list[parser.ParsedRow]
) -> dict[int, Transaction]:
    """RB-006: cada linha do arquivo casa com NO MÁXIMO um lançamento existente, e
    cada lançamento existente casa com no máximo uma linha. Sem isso, duas compras
    legítimas iguais no mesmo dia seriam ambas marcadas como duplicata de uma só.
    """
    valid = [r for r in rows if r.error is None and r.occurred_at and r.amount is not None and r.type]
    if not valid:
        return {}

    window = timedelta(days=DUPLICATE_WINDOW_DAYS)
    existing = transactions_service.list_by_account_period(
        db,
        user_id,
        account_id,
        min(r.occurred_at for r in valid) - window,
        max(r.occurred_at for r in valid) + window,
    )
    by_key: dict[tuple[str, Decimal], list[Transaction]] = defaultdict(list)
    for transaction in existing:
        by_key[(transaction.type.value, transaction.amount)].append(transaction)

    matches: dict[int, Transaction] = {}
    for row in valid:
        candidates = [
            t for t in by_key.get((row.type, row.amount), []) if abs(t.occurred_at - row.occurred_at) <= window
        ]
        if not candidates:
            continue
        best = min(candidates, key=lambda t: (abs(t.occurred_at - row.occurred_at), t.occurred_at))
        by_key[(row.type, row.amount)].remove(best)
        matches[row.row_number] = best
    return matches


def preview(
    db: Session,
    user_id: uuid.UUID,
    account_id: uuid.UUID,
    raw: bytes,
    mapping: ColumnMapping | None,
) -> PreviewResult:
    _check_account(db, user_id, account_id)

    file_sha256 = hashlib.sha256(raw).hexdigest()
    parsed = parser.parse_csv(raw, mapping)
    previous = repository.find_latest_by_hash(db, user_id, account_id, file_sha256)
    return PreviewResult(
        file_sha256=file_sha256,
        parsed=parsed,
        duplicates=find_duplicates(db, user_id, account_id, parsed.rows),
        previously_imported_at=previous.created_at if previous else None,
    )


@dataclass(frozen=True)
class ConfirmedRow:
    occurred_at: date
    type: str
    amount: Decimal
    description: str | None
    category_id: uuid.UUID


def confirm_import(
    db: Session,
    user_id: uuid.UUID,
    account_id: uuid.UUID,
    file_name: str,
    file_sha256: str,
    rows_total: int,
    rows: list[ConfirmedRow],
) -> StatementImport:
    """Cria os lançamentos escolhidos e o registro da importação numa transação só.

    Posse da conta/categorias é revalidada aqui (via transactions.create_many):
    nada que veio da pré-visualização é confiável.
    """
    drafts = [
        transactions_service.TransactionDraft(
            category_id=row.category_id,
            type=TransactionType(row.type),
            amount=row.amount,
            description=row.description,
            occurred_at=row.occurred_at,
        )
        for row in rows
    ]
    try:
        transactions_service.create_many(
            db, user_id, account_id, drafts, source=TransactionSource.IMPORT, commit=False
        )
    except transactions_service.InvalidAccountError:
        raise AccountNotFoundError(account_id)

    statement_import = StatementImport(
        user_id=user_id,
        account_id=account_id,
        file_name=file_name,
        file_sha256=file_sha256,
        rows_total=rows_total,
        transactions_created=len(rows),
        rows_skipped=rows_total - len(rows),
    )
    repository.add(db, statement_import)
    db.commit()
    db.refresh(statement_import)
    return statement_import
