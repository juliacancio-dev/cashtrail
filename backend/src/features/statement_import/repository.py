import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.features.statement_import.models import StatementImport


def add(db: Session, statement_import: StatementImport) -> None:
    """Só adiciona à sessão: o commit é do service, junto com os lançamentos."""
    db.add(statement_import)


def find_latest_by_hash(
    db: Session, user_id: uuid.UUID, account_id: uuid.UUID, file_sha256: str
) -> StatementImport | None:
    return db.scalar(
        select(StatementImport)
        .where(
            StatementImport.user_id == user_id,
            StatementImport.account_id == account_id,
            StatementImport.file_sha256 == file_sha256,
        )
        .order_by(StatementImport.created_at.desc())
        .limit(1)
    )
