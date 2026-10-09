import calendar
import uuid
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from src.features.accounts import service as accounts_service
from src.features.categories import service as categories_service
from src.features.commitments import service as commitments_service
from src.features.commitments.models import CommitmentDirection
from src.features.recurring import repository
from src.features.recurring.models import RecurringFrequency, RecurringTransaction
from src.features.transactions import service as transactions_service
from src.features.transactions.models import TransactionSource, TransactionType


# Recorrência no modo "conta a pagar/receber": cria o compromisso com esta antecedência,
# para ele aparecer na lista (e no alerta de vencimentos) antes de vencer.
COMMITMENT_LOOKAHEAD_DAYS = 31
# Trava de segurança por execução: uma recorrência semanal criada com data muito antiga
# não pode gerar centenas de compromissos de uma vez.
MAX_COMMITMENTS_PER_RUN = 12


class RecurringNotFoundError(Exception):
    pass


class InvalidAccountError(Exception):
    pass


class InvalidCategoryError(Exception):
    pass


class ArchivedAccountError(Exception):
    pass


def _advance(current: date, frequency: RecurringFrequency) -> date:
    if frequency == RecurringFrequency.WEEKLY:
        return current + timedelta(days=7)

    # monthly: avança um mês, corrigindo dias que não existem no mês seguinte (ex: 31 -> 28/29/30)
    month = current.month + 1
    year = current.year + (month - 1) // 12
    month = (month - 1) % 12 + 1
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(current.day, last_day))


def list_recurring(db: Session, user_id: uuid.UUID) -> list[RecurringTransaction]:
    return repository.list_by_user(db, user_id)


def get_recurring(db: Session, user_id: uuid.UUID, recurring_id: uuid.UUID) -> RecurringTransaction:
    recurring = repository.get_by_id_and_user(db, recurring_id, user_id)
    if recurring is None:
        raise RecurringNotFoundError(recurring_id)

    return recurring


def create_recurring(
    db: Session,
    user_id: uuid.UUID,
    account_id: uuid.UUID,
    category_id: uuid.UUID,
    type: TransactionType,
    amount: Decimal,
    description: str | None,
    frequency: RecurringFrequency,
    next_occurrence_date: date,
    generate_as_commitment: bool = False,
) -> RecurringTransaction:
    """Mesma validação de posse/estado de conta que transactions.create_transaction (RB-001)."""
    try:
        account = accounts_service.get_account(db, user_id, account_id)
    except accounts_service.AccountNotFoundError:
        raise InvalidAccountError(account_id)

    if account.is_archived:
        raise ArchivedAccountError(account_id)

    try:
        categories_service.get_category(db, user_id, category_id)
    except categories_service.CategoryNotFoundError:
        raise InvalidCategoryError(category_id)

    return repository.create(
        db,
        user_id=user_id,
        account_id=account_id,
        category_id=category_id,
        type=type,
        amount=amount,
        description=description,
        frequency=frequency,
        next_occurrence_date=next_occurrence_date,
        generate_as_commitment=generate_as_commitment,
    )


def update_recurring(
    db: Session,
    user_id: uuid.UUID,
    recurring_id: uuid.UUID,
    amount: Decimal | None,
    description: str | None,
    frequency: RecurringFrequency | None,
) -> RecurringTransaction:
    recurring = get_recurring(db, user_id, recurring_id)
    return repository.update(db, recurring, amount, description, frequency)


def deactivate_recurring(db: Session, user_id: uuid.UUID, recurring_id: uuid.UUID) -> RecurringTransaction:
    """RB-004: só um cancelamento explícito interrompe a geração futura."""
    recurring = get_recurring(db, user_id, recurring_id)
    return repository.deactivate(db, recurring)


def generate_due_transactions(db: Session, as_of: date | None = None) -> int:
    """Job agendado (ADR-005/APScheduler): para toda recorrência ativa vencida,
    gera o lançamento via transactions.service (nunca insere direto na tabela,
    09-vertical-slices.md) e avança a próxima ocorrência. Roda para todos os
    usuários — não é uma requisição autenticada.
    """
    as_of = as_of or date.today()
    due = repository.list_due(db, as_of)

    generated = 0
    for recurring in due:
        try:
            transactions_service.create_transaction(
                db,
                recurring.user_id,
                account_id=recurring.account_id,
                category_id=recurring.category_id,
                type=recurring.type,
                amount=recurring.amount,
                description=recurring.description,
                occurred_at=recurring.next_occurrence_date,
                source=TransactionSource.RECURRING,
                recurring_transaction_id=recurring.id,
            )
        except (
            transactions_service.InvalidAccountError,
            transactions_service.InvalidCategoryError,
            transactions_service.ArchivedAccountError,
        ):
            # conta/categoria ficou inválida depois que a recorrência foi criada —
            # não avança a data, tenta de novo na próxima execução do job.
            continue

        repository.advance_next_occurrence(db, recurring, _advance(recurring.next_occurrence_date, recurring.frequency))
        generated += 1

    return generated


def generate_due_commitments(db: Session, as_of: date | None = None) -> int:
    """Job agendado (RF-022): recorrências no modo "conta a pagar/receber" criam o
    compromisso de cada ocorrência até COMMITMENT_LOOKAHEAD_DAYS à frente.

    Idempotente: se o compromisso daquela ocorrência já existe (job que caiu entre criar
    e avançar a data), não duplica, só avança. Passa por commitments.service, nunca
    insere direto na tabela (09-vertical-slices.md).
    """
    as_of = as_of or date.today()
    horizon = as_of + timedelta(days=COMMITMENT_LOOKAHEAD_DAYS)

    generated = 0
    for recurring in repository.list_due(db, horizon, as_commitment=True):
        for _ in range(MAX_COMMITMENTS_PER_RUN):
            due_date = recurring.next_occurrence_date
            if due_date > horizon:
                break

            if not commitments_service.has_commitment_for_recurrence(db, recurring.user_id, recurring.id, due_date):
                try:
                    description = recurring.description or categories_service.get_category(
                        db, recurring.user_id, recurring.category_id
                    ).name
                    commitments_service.create_commitment(
                        db,
                        recurring.user_id,
                        direction=(
                            CommitmentDirection.PAYABLE
                            if recurring.type == TransactionType.EXPENSE
                            else CommitmentDirection.RECEIVABLE
                        ),
                        description=description,
                        counterparty=None,
                        amount=recurring.amount,
                        due_date=due_date,
                        category_id=recurring.category_id,
                        account_id=recurring.account_id,
                        notes=None,
                        recurring_transaction_id=recurring.id,
                    )
                except (
                    categories_service.CategoryNotFoundError,
                    commitments_service.InvalidAccountError,
                    commitments_service.InvalidCategoryError,
                    commitments_service.ArchivedAccountError,
                ):
                    # conta/categoria ficou inválida: não avança, tenta de novo na próxima execução.
                    break
                generated += 1

            repository.advance_next_occurrence(db, recurring, _advance(due_date, recurring.frequency))

    return generated

@dataclass(frozen=True)
class Occurrence:
    """Ocorrência FUTURA de uma recorrência, calculada pela regra (ainda não gerada)."""

    recurring_id: uuid.UUID
    occurs_on: date
    type: TransactionType
    amount: Decimal
    description: str | None
    category_id: uuid.UUID
    account_id: uuid.UUID
    generate_as_commitment: bool


# Trava por recorrência: uma regra semanal projetada por anos não pode gerar milhares de itens.
MAX_PROJECTED_OCCURRENCES = 120


def list_future_occurrences(db: Session, user_id: uuid.UUID, until: date) -> list[Occurrence]:
    """Expande as regras ativas em ocorrências até `until` (Marco 10, decisão 4).

    Começa em `next_occurrence_date`, que é a primeira ocorrência AINDA NÃO gerada, então
    nada aqui duplica um lançamento ou compromisso que já existe.
    """
    occurrences: list[Occurrence] = []
    for recurring in repository.list_by_user(db, user_id):
        if not recurring.is_active:
            continue
        current = recurring.next_occurrence_date
        for _ in range(MAX_PROJECTED_OCCURRENCES):
            if current > until:
                break
            occurrences.append(
                Occurrence(
                    recurring_id=recurring.id,
                    occurs_on=current,
                    type=recurring.type,
                    amount=recurring.amount,
                    description=recurring.description,
                    category_id=recurring.category_id,
                    account_id=recurring.account_id,
                    generate_as_commitment=recurring.generate_as_commitment,
                )
            )
            current = _advance(current, recurring.frequency)
    return occurrences