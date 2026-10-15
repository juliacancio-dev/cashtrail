import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.features.accounts import service as accounts_service
from src.features.assets import service as assets_service
from src.features.categories import service as categories_service
from src.features.commitments import service as commitments_service
from src.features.commitments.models import CommitmentDirection
from src.features.insurance.models import POLICY_KINDS, PREMIUM_FREQUENCIES, InsurancePolicy
from src.features.recurring import service as recurring_service
from src.features.recurring.models import RecurringFrequency
from src.features.transactions.models import TransactionType

RENEWAL_ALERT_DAYS = 30


class PolicyNotFoundError(Exception):
    pass


class InvalidAccountError(Exception):
    pass


class ArchivedAccountError(Exception):
    pass


class InvalidCategoryError(Exception):
    pass


class InvalidAssetError(Exception):
    pass


class InvalidPolicyError(Exception):
    """Tipo ou periodicidade inválidos."""


class PolicyInactiveError(Exception):
    pass


@dataclass(frozen=True)
class PolicyView:
    policy: InsurancePolicy
    days_to_renewal: int
    renewal_status: str  # ok | soon | overdue | inactive


@dataclass(frozen=True)
class UninsuredAsset:
    asset_id: uuid.UUID
    name: str
    kind: str
    value: Decimal


@dataclass(frozen=True)
class Summary:
    active_count: int
    renewals_soon: list[PolicyView]
    overdue_renewals: list[PolicyView]
    uninsured_assets: list[UninsuredAsset]
    monthly_cost: Decimal  # prêmios ativos normalizados para o mês (anual ÷ 12)


def _add_year(day: date) -> date:
    try:
        return day.replace(year=day.year + 1)
    except ValueError:  # 29/02
        return day.replace(year=day.year + 1, day=28)


def _status(policy: InsurancePolicy, today: date) -> PolicyView:
    days = (policy.renews_on - today).days
    if not policy.is_active:
        return PolicyView(policy, days, "inactive")
    if days < 0:
        return PolicyView(policy, days, "overdue")
    if days <= RENEWAL_ALERT_DAYS:
        return PolicyView(policy, days, "soon")
    return PolicyView(policy, days, "ok")


def _get(db: Session, user_id: uuid.UUID, policy_id: uuid.UUID) -> InsurancePolicy:
    policy = db.scalar(
        select(InsurancePolicy).where(InsurancePolicy.id == policy_id, InsurancePolicy.user_id == user_id)
    )
    if policy is None:
        raise PolicyNotFoundError(policy_id)
    return policy


def _validate_refs(
    db: Session, user_id: uuid.UUID, account_id: uuid.UUID | None, category_id: uuid.UUID | None,
    asset_id: uuid.UUID | None,
) -> None:
    if account_id is not None:
        try:
            account = accounts_service.get_account(db, user_id, account_id)
        except accounts_service.AccountNotFoundError:
            raise InvalidAccountError(account_id)
        if account.is_archived:
            raise ArchivedAccountError(account_id)
    if category_id is not None:
        try:
            categories_service.get_category(db, user_id, category_id)
        except categories_service.CategoryNotFoundError:
            raise InvalidCategoryError(category_id)
    if asset_id is not None:
        try:
            assets_service.get_asset(db, user_id, asset_id)
        except assets_service.AssetNotFoundError:
            raise InvalidAssetError(asset_id)


def list_policies(db: Session, user_id: uuid.UUID, today: date | None = None) -> list[PolicyView]:
    today = today or date.today()
    rows = db.scalars(
        select(InsurancePolicy).where(InsurancePolicy.user_id == user_id).order_by(
            InsurancePolicy.is_active.desc(), InsurancePolicy.renews_on
        )
    )
    return [_status(p, today) for p in rows]


def get_policy(db: Session, user_id: uuid.UUID, policy_id: uuid.UUID, today: date | None = None) -> PolicyView:
    return _status(_get(db, user_id, policy_id), today or date.today())


def _create_premium(
    db: Session, user_id: uuid.UUID, policy: InsurancePolicy, today: date, due: date
) -> None:
    """RF-069/RB-044: mensal vira recorrência com conta a pagar; anual vira conta a pagar no vencimento."""
    description = f"Seguro {policy.name}"[:255]
    if policy.premium_frequency == "monthly":
        recurring = recurring_service.create_recurring(
            db,
            user_id,
            account_id=policy.payment_account_id,
            category_id=policy.category_id,
            type=TransactionType.EXPENSE,
            amount=policy.premium_amount,
            description=description,
            frequency=RecurringFrequency.MONTHLY,
            next_occurrence_date=due,
            generate_as_commitment=True,
        )
        policy.recurring_id = recurring.id
    else:
        [view] = commitments_service.create_commitment(
            db,
            user_id,
            direction=CommitmentDirection.PAYABLE,
            description=description,
            counterparty=policy.insurer,
            amount=policy.premium_amount,
            due_date=due,
            category_id=policy.category_id,
            account_id=policy.payment_account_id,
            notes=None,
            installments=1,
            today=today,
        )
        policy.commitment_id = view.commitment.id


def create_policy(
    db: Session,
    user_id: uuid.UUID,
    kind: str,
    insurer: str,
    name: str,
    premium_amount: Decimal,
    premium_frequency: str,
    coverage_amount: Decimal | None,
    starts_on: date | None,
    renews_on: date,
    first_due_on: date | None,
    asset_id: uuid.UUID | None,
    payment_account_id: uuid.UUID,
    category_id: uuid.UUID,
    notes: str | None,
    today: date | None = None,
) -> PolicyView:
    today = today or date.today()
    if kind not in POLICY_KINDS or premium_frequency not in PREMIUM_FREQUENCIES:
        raise InvalidPolicyError(kind)
    _validate_refs(db, user_id, payment_account_id, category_id, asset_id)

    policy = InsurancePolicy(
        user_id=user_id,
        kind=kind,
        insurer=insurer,
        name=name,
        premium_amount=premium_amount,
        premium_frequency=premium_frequency,
        coverage_amount=coverage_amount,
        starts_on=starts_on,
        renews_on=renews_on,
        first_due_on=first_due_on,
        asset_id=asset_id,
        payment_account_id=payment_account_id,
        category_id=category_id,
        notes=notes,
    )
    due = (first_due_on or today) if premium_frequency == "monthly" else renews_on
    _create_premium(db, user_id, policy, today, due)
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return _status(policy, today)


def update_policy(
    db: Session, user_id: uuid.UUID, policy_id: uuid.UUID, changes: dict[str, Any], today: date | None = None
) -> PolicyView:
    """Mudar o prêmio atualiza a recorrência (mensal) ou a conta a pagar em aberto (anual)."""
    today = today or date.today()
    policy = _get(db, user_id, policy_id)
    if "kind" in changes and changes["kind"] not in POLICY_KINDS:
        raise InvalidPolicyError(changes["kind"])
    if "asset_id" in changes:
        _validate_refs(db, user_id, None, None, changes["asset_id"])

    for field in ("name", "insurer", "kind", "coverage_amount", "renews_on", "asset_id", "notes"):
        if field in changes:
            setattr(policy, field, changes[field])

    if "premium_amount" in changes and changes["premium_amount"] != policy.premium_amount:
        policy.premium_amount = changes["premium_amount"]
        _sync_premium(db, user_id, policy, today)
    db.commit()
    db.refresh(policy)
    return _status(policy, today)


def _sync_premium(db: Session, user_id: uuid.UUID, policy: InsurancePolicy, today: date) -> None:
    if policy.premium_frequency == "monthly" and policy.recurring_id is not None:
        recurring_service.update_recurring(db, user_id, policy.recurring_id, policy.premium_amount, None, None)
    elif policy.premium_frequency == "annual" and policy.commitment_id is not None:
        try:
            commitments_service.update_commitment(
                db, user_id, policy.commitment_id, {"amount": policy.premium_amount}, today=today
            )
        except commitments_service.CommitmentLockedError:
            pass  # ciclo já pago: o novo valor vale para a próxima renovação


def renew_policy(
    db: Session,
    user_id: uuid.UUID,
    policy_id: uuid.UUID,
    new_premium: Decimal | None,
    today: date | None = None,
) -> PolicyView:
    """RF-070: avança a vigência em um ano e, se anual, cria o prêmio do novo ciclo."""
    today = today or date.today()
    policy = _get(db, user_id, policy_id)
    if not policy.is_active:
        raise PolicyInactiveError(policy_id)

    if new_premium is not None and new_premium != policy.premium_amount:
        policy.premium_amount = new_premium
        if policy.premium_frequency == "monthly":
            _sync_premium(db, user_id, policy, today)
        # Anual: o valor novo vale para o ciclo que começa agora; o prêmio do ciclo anterior não muda.

    policy.renews_on = _add_year(policy.renews_on)
    if policy.premium_frequency == "annual":
        _create_premium(db, user_id, policy, today, policy.renews_on)
    db.commit()
    db.refresh(policy)
    return _status(policy, today)


def deactivate_policy(
    db: Session, user_id: uuid.UUID, policy_id: uuid.UUID, today: date | None = None
) -> PolicyView:
    """Encerra: para a recorrência (mensal) ou cancela a conta a pagar em aberto (anual)."""
    today = today or date.today()
    policy = _get(db, user_id, policy_id)
    if policy.premium_frequency == "monthly" and policy.recurring_id is not None:
        recurring_service.deactivate_recurring(db, user_id, policy.recurring_id)
    elif policy.premium_frequency == "annual" and policy.commitment_id is not None:
        try:
            commitments_service.cancel_commitment(db, user_id, policy.commitment_id, today=today)
        except commitments_service.CommitmentLockedError:
            pass  # já paga ou cancelada
    policy.is_active = False
    db.commit()
    db.refresh(policy)
    return _status(policy, today)


def summary(db: Session, user_id: uuid.UUID, today: date | None = None) -> Summary:
    """RF-071/RF-075: renovações próximas, vencidas e bens ativos sem apólice ativa."""
    today = today or date.today()
    views = list_policies(db, user_id, today)
    active = [v for v in views if v.policy.is_active]
    insured = {v.policy.asset_id for v in active if v.policy.asset_id is not None}

    uninsured = [
        UninsuredAsset(a.asset.id, a.asset.name, a.asset.kind, a.value)
        for a in assets_service.list_views(db, user_id, today)
        if a.value > 0 and a.asset.disposed_at is None and a.asset.id not in insured
    ]
    monthly = sum(
        (
            v.policy.premium_amount if v.policy.premium_frequency == "monthly" else v.policy.premium_amount / 12
            for v in active
        ),
        Decimal("0"),
    ).quantize(Decimal("0.01"))
    return Summary(
        active_count=len(active),
        renewals_soon=[v for v in active if v.renewal_status == "soon"],
        overdue_renewals=[v for v in active if v.renewal_status == "overdue"],
        uninsured_assets=uninsured,
        monthly_cost=monthly,
    )
