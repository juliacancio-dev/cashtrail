import uuid
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from src.features.accounts import service as accounts_service
from src.features.accounts.models import Account, AccountType
from src.features.categories import service as categories_service
from src.features.commitments import service as commitments_service
from src.features.commitments.models import Commitment, CommitmentDirection
from src.features.debts import repository, schedule
from src.features.debts.models import Debt, DebtAmortization, DebtInstallment
from src.features.transfers import service as transfers_service

ZERO = Decimal("0.00")
SOON_DAYS = 7
MAX_INSTALLMENTS = 360


class DebtNotFoundError(Exception):
    pass


class InstallmentNotFoundError(Exception):
    pass


class InvalidAccountError(Exception):
    pass


class InvalidCategoryError(Exception):
    pass


class ArchivedAccountError(Exception):
    pass


class InvalidScheduleError(Exception):
    """Parâmetros que não geram cronograma (parcelas fora de 1-360, parcela que não cobre juros...)."""


class InvalidAmountError(Exception):
    """Amortização/parcela acima do saldo devedor, ou valor de parcela abaixo do principal dela."""


class FutureDateError(Exception):
    pass


class AccountRequiredError(Exception):
    pass


class InstallmentLockedError(Exception):
    """Parcela já paga, cancelada ou substituída por um recálculo."""


class DebtPaidOffError(Exception):
    pass


class NoPaymentError(Exception):
    pass


@dataclass
class InstallmentView:
    installment: DebtInstallment
    commitment: Commitment
    paid: Decimal
    status: str  # open | due_today | overdue | paid | canceled | superseded

    @property
    def amount(self) -> Decimal:
        return self.commitment.amount

    @property
    def charges(self) -> Decimal:
        return self.commitment.amount - self.installment.principal_part


@dataclass
class DebtView:
    debt: Debt
    account: Account
    outstanding: Decimal
    principal_paid: Decimal
    charges_paid: Decimal
    charges_projected: Decimal
    installments_paid: int
    installments_open: int
    next_installment: InstallmentView | None
    is_paid_off: bool


@dataclass
class DebtDetail:
    view: DebtView
    installments: list[InstallmentView]
    amortizations: list[DebtAmortization]
    settlements: dict[uuid.UUID, uuid.UUID] = field(default_factory=dict)  # installment id -> settlement id


@dataclass(frozen=True)
class PlannedInstallment:
    number: int
    due_date: date
    principal: Decimal
    charges: Decimal
    amount: Decimal
    balance: Decimal


@dataclass(frozen=True)
class AmortizationPlan:
    outstanding_before: Decimal
    outstanding_after: Decimal
    rows: list[PlannedInstallment]
    charges_before: Decimal
    charges_after: Decimal
    installments_before: int


# ---------- helpers ----------

def _fraction(percent: Decimal) -> Decimal:
    return percent / Decimal(100)


def _check_account(db: Session, user_id: uuid.UUID, account_id: uuid.UUID) -> Account:
    try:
        account = accounts_service.get_account(db, user_id, account_id)
    except accounts_service.AccountNotFoundError:
        raise InvalidAccountError(account_id)
    if account.is_archived or account.type in (AccountType.CREDIT_CARD, AccountType.LOAN):
        raise ArchivedAccountError(account_id) if account.is_archived else InvalidAccountError(account_id)
    return account


def _get_debt(db: Session, user_id: uuid.UUID, debt_id: uuid.UUID) -> Debt:
    debt = repository.get_debt(db, debt_id, user_id)
    if debt is None:
        raise DebtNotFoundError(debt_id)
    return debt


def _outstanding(db: Session, user_id: uuid.UUID, debt: Debt, account: Account) -> Decimal:
    """Saldo devedor = −saldo da conta `loan` (inicial + recebido − enviado)."""
    balance = (
        account.opening_balance
        + transfers_service.sum_into_account(db, user_id, account.id)
        - transfers_service.sum_out_of_account(db, user_id, account.id)
    )
    return max(-balance, ZERO).quantize(Decimal("0.01"))


def _status(commitment: Commitment, paid: Decimal, installment: DebtInstallment, today: date) -> str:
    if installment.is_superseded:
        return "superseded"
    return commitments_service.derive_status(commitment, paid, today)


def _installment_views(db: Session, user_id: uuid.UUID, debt: Debt, today: date) -> list[InstallmentView]:
    rows = repository.list_installments(db, debt.id, user_id)
    views, _ = commitments_service.list_commitments(db, user_id, today=today)
    by_id = {v.commitment.id: v for v in views}
    result: list[InstallmentView] = []
    for installment in rows:
        view = by_id.get(installment.commitment_id)
        if view is None:
            continue
        result.append(
            InstallmentView(installment, view.commitment, view.paid_amount, _status(view.commitment, view.paid_amount, installment, today))
        )
    return result


def _build_view(
    db: Session, user_id: uuid.UUID, debt: Debt, installments: list[InstallmentView], today: date
) -> DebtView:
    account = accounts_service.get_account(db, user_id, debt.account_id)
    live = [i for i in installments if i.status != "superseded"]
    paid = [i for i in live if i.status == "paid"]
    open_ = [i for i in live if i.status in ("open", "due_today", "overdue", "partially_paid")]
    outstanding = _outstanding(db, user_id, debt, account)
    next_open = min(open_, key=lambda i: (i.commitment.due_date, i.installment.number), default=None)
    return DebtView(
        debt=debt,
        account=account,
        outstanding=outstanding,
        principal_paid=sum((i.installment.principal_part for i in paid), ZERO),
        charges_paid=sum((i.charges for i in paid), ZERO),
        charges_projected=sum((i.charges for i in open_), ZERO),
        installments_paid=len(paid),
        installments_open=len(open_),
        next_installment=next_open,
        is_paid_off=outstanding <= 0 and not open_,
    )


# ---------- cronograma ----------

def preview_schedule(
    principal: Decimal, installments: int, first_due_date: date, system: str, monthly_rate: Decimal
) -> list[PlannedInstallment]:
    """RF-033: simulação sem gravar nada."""
    if not 1 <= installments <= MAX_INSTALLMENTS:
        raise InvalidScheduleError(installments)
    try:
        rows = schedule.build(principal, system, _fraction(monthly_rate), installments)
    except schedule.ScheduleError as exc:
        raise InvalidScheduleError(str(exc))
    return [
        PlannedInstallment(
            row.number,
            commitments_service.add_months(first_due_date, row.number - 1),
            row.principal,
            row.interest,
            row.payment,
            row.balance,
        )
        for row in rows
    ]


# ---------- dívida ----------

def create_debt(
    db: Session,
    user_id: uuid.UUID,
    name: str,
    creditor: str | None,
    principal: Decimal,
    contracted_at: date,
    installments: int,
    first_due_date: date,
    system: str,
    monthly_rate: Decimal,
    interest_category_id: uuid.UUID,
    payment_account_id: uuid.UUID | None,
    received_account_id: uuid.UUID | None,
    today: date | None = None,
) -> DebtView:
    """RF-032/RF-033/RF-035. Cria a conta `loan`, a configuração e as parcelas como contas a pagar.

    Com `received_account_id`, o dinheiro entra por uma TRANSFERÊNCIA da conta da dívida (RB-023: não é
    receita). Sem ele, a dívida já existia: a conta nasce com saldo inicial −principal.
    """
    today = today or date.today()
    plan = preview_schedule(principal, installments, first_due_date, system, monthly_rate)

    try:
        categories_service.get_category(db, user_id, interest_category_id)
    except categories_service.CategoryNotFoundError:
        raise InvalidCategoryError(interest_category_id)
    if payment_account_id is not None:
        _check_account(db, user_id, payment_account_id)
    if received_account_id is not None:
        _check_account(db, user_id, received_account_id)
        if contracted_at > today:
            raise FutureDateError(contracted_at)

    account = accounts_service.create_account(
        db,
        user_id,
        name=name,
        type=AccountType.LOAN,
        opening_balance=ZERO if received_account_id else -principal,
    )
    debt = Debt(
        user_id=user_id,
        account_id=account.id,
        creditor=creditor,
        principal=principal,
        contracted_at=contracted_at,
        installments=installments,
        system=system,
        monthly_rate=monthly_rate,
        first_due_date=first_due_date,
        payment_account_id=payment_account_id,
        interest_category_id=interest_category_id,
    )
    repository.add(db, debt)

    if received_account_id is not None:
        transfers_service.create_transfer(
            db,
            user_id,
            from_account_id=account.id,
            to_account_id=received_account_id,
            amount=principal,
            occurred_at=contracted_at,
            description=f"Recebimento: {name}"[:255],
            commit=False,
            today=today,
        )

    _create_installments(db, user_id, debt, name, plan, start_number=1, total=installments, today=today)
    db.commit()
    db.refresh(debt)
    return get_debt(db, user_id, debt.id, today).view


def _create_installments(
    db: Session,
    user_id: uuid.UUID,
    debt: Debt,
    name: str,
    plan: list[PlannedInstallment],
    start_number: int,
    total: int,
    today: date,
) -> None:
    for offset, row in enumerate(plan):
        number = start_number + offset
        [view] = commitments_service.create_commitment(
            db,
            user_id,
            direction=CommitmentDirection.PAYABLE,
            description=name,
            counterparty=debt.creditor,
            amount=row.amount,
            due_date=row.due_date,
            category_id=debt.interest_category_id,
            account_id=debt.payment_account_id,
            notes=None,
            installments=1,
            today=today,
            debt_id=debt.id,
            installment_number=number,
            installment_count=total,
            commit=False,
        )
        repository.add(
            db,
            DebtInstallment(
                user_id=user_id,
                debt_id=debt.id,
                number=number,
                commitment_id=view.commitment.id,
                principal_part=row.principal,
            ),
        )


def list_debts(db: Session, user_id: uuid.UUID, today: date | None = None) -> list[DebtView]:
    today = today or date.today()
    return [
        _build_view(db, user_id, debt, _installment_views(db, user_id, debt, today), today)
        for debt in repository.list_debts(db, user_id)
    ]


def get_debt(db: Session, user_id: uuid.UUID, debt_id: uuid.UUID, today: date | None = None) -> DebtDetail:
    today = today or date.today()
    debt = _get_debt(db, user_id, debt_id)
    installments = _installment_views(db, user_id, debt, today)
    settlements: dict[uuid.UUID, uuid.UUID] = {}
    for item in installments:
        if item.status == "paid":
            _, rows = commitments_service.get_commitment(db, user_id, item.commitment.id, today)
            if rows:
                settlements[item.installment.id] = rows[-1].id
    return DebtDetail(
        view=_build_view(db, user_id, debt, installments, today),
        installments=installments,
        amortizations=repository.list_amortizations(db, debt.id, user_id),
        settlements=settlements,
    )


def summary(db: Session, user_id: uuid.UUID, today: date | None = None, days: int = SOON_DAYS) -> dict[str, Any]:
    """RF-039: saldo devedor total e a próxima parcela, para o dashboard."""
    today = today or date.today()
    views = list_debts(db, user_id, today)
    active = [v for v in views if not v.is_paid_off]
    upcoming = [v.next_installment for v in active if v.next_installment is not None]
    nxt = min(upcoming, key=lambda i: i.commitment.due_date, default=None)
    overdue = 0
    for view in active:
        item = view.next_installment
        if item is not None and item.status == "overdue":
            overdue += 1
    return {
        "outstanding_total": sum((v.outstanding for v in active), ZERO),
        "active_count": len(active),
        "overdue_count": overdue,
        "next_due_date": nxt.commitment.due_date if nxt else None,
        "next_amount": nxt.amount if nxt else None,
        "next_debt_name": next((v.account.name for v in active if v.next_installment is nxt), None) if nxt else None,
    }


# ---------- parcelas ----------

def _installment(db: Session, user_id: uuid.UUID, debt: Debt, installment_id: uuid.UUID) -> DebtInstallment:
    installment = repository.get_installment(db, installment_id, debt.id, user_id)
    if installment is None:
        raise InstallmentNotFoundError(installment_id)
    return installment


def update_installment(
    db: Session,
    user_id: uuid.UUID,
    debt_id: uuid.UUID,
    installment_id: uuid.UUID,
    changes: dict[str, Any],
    today: date | None = None,
) -> InstallmentView:
    """RF-034: o valor só pode ser ≥ principal da parcela; a diferença são os encargos."""
    today = today or date.today()
    debt = _get_debt(db, user_id, debt_id)
    installment = _installment(db, user_id, debt, installment_id)
    if installment.is_superseded:
        raise InstallmentLockedError(installment_id)
    if "amount" in changes and changes["amount"] < installment.principal_part:
        raise InvalidAmountError(installment_id)

    allowed = {k: v for k, v in changes.items() if k in ("amount", "due_date")}
    try:
        commitments_service.update_commitment(
            db, user_id, installment.commitment_id, allowed, today=today, via_debt=True
        )
    except commitments_service.CommitmentLockedError:
        raise InstallmentLockedError(installment_id)
    return next(v for v in _installment_views(db, user_id, debt, today) if v.installment.id == installment.id)


def pay_installment(
    db: Session,
    user_id: uuid.UUID,
    debt_id: uuid.UUID,
    installment_id: uuid.UUID,
    paid_at: date | None,
    from_account_id: uuid.UUID | None,
    today: date | None = None,
) -> InstallmentView:
    """RF-036/RB-023/RB-024: o principal vira transferência para a conta da dívida e só os
    encargos viram despesa (na categoria de juros), então o DRE não conta o principal."""
    today = today or date.today()
    debt = _get_debt(db, user_id, debt_id)
    installment = _installment(db, user_id, debt, installment_id)
    if installment.is_superseded:
        raise InstallmentLockedError(installment_id)

    account = accounts_service.get_account(db, user_id, debt.account_id)
    if installment.principal_part > _outstanding(db, user_id, debt, account):
        raise InvalidAmountError(installment_id)  # RB-026

    try:
        commitments_service.settle_commitment(
            db,
            user_id,
            installment.commitment_id,
            amount=None,
            paid_at=paid_at,
            account_id=from_account_id,
            today=today,
            transfer_amount=installment.principal_part,
            transfer_to_account_id=debt.account_id,
        )
    except commitments_service.CommitmentLockedError:
        raise InstallmentLockedError(installment_id)
    except commitments_service.AccountRequiredError:
        raise AccountRequiredError(installment_id)
    except commitments_service.FutureDateError:
        raise FutureDateError(paid_at)
    except commitments_service.ArchivedAccountError:
        raise ArchivedAccountError(from_account_id)
    except commitments_service.InvalidAccountError:
        raise InvalidAccountError(from_account_id)
    return next(v for v in _installment_views(db, user_id, debt, today) if v.installment.id == installment.id)


def undo_payment(
    db: Session, user_id: uuid.UUID, debt_id: uuid.UUID, installment_id: uuid.UUID, today: date | None = None
) -> InstallmentView:
    today = today or date.today()
    debt = _get_debt(db, user_id, debt_id)
    installment = _installment(db, user_id, debt, installment_id)
    _, settlements = commitments_service.get_commitment(db, user_id, installment.commitment_id, today)
    if not settlements:
        raise NoPaymentError(installment_id)
    commitments_service.undo_settlement(db, user_id, installment.commitment_id, settlements[-1].id, today)
    return next(v for v in _installment_views(db, user_id, debt, today) if v.installment.id == installment.id)


# ---------- amortização extra e quitação ----------

def _open_installments(views: list[InstallmentView]) -> list[InstallmentView]:
    return sorted(
        (v for v in views if v.status in ("open", "due_today", "overdue")),
        key=lambda v: (v.commitment.due_date, v.installment.number),
    )


def _plan(
    db: Session,
    user_id: uuid.UUID,
    debt: Debt,
    amount: Decimal,
    mode: str,
    today: date,
) -> tuple[AmortizationPlan, list[InstallmentView]]:
    account = accounts_service.get_account(db, user_id, debt.account_id)
    outstanding = _outstanding(db, user_id, debt, account)
    if outstanding <= 0:
        raise DebtPaidOffError(debt.id)
    if mode == "payoff":
        amount = outstanding
    if amount <= 0 or amount > outstanding:
        raise InvalidAmountError(debt.id)

    views = _installment_views(db, user_id, debt, today)
    open_ = _open_installments(views)
    after = (outstanding - amount).quantize(Decimal("0.01"))
    rate = Decimal(0) if debt.system == "zero" else _fraction(debt.monthly_rate)

    rows: list[schedule.Row] = []
    if after > 0:
        try:
            if mode == "reduce_installment" or not open_:
                rows = schedule.build(after, debt.system, rate, max(len(open_), 1))
            elif debt.system == "sac":
                rows = schedule.constant_amortization(after, rate, open_[0].installment.principal_part)
            else:
                interest_now = schedule.money(outstanding * rate)
                payment = open_[0].installment.principal_part + interest_now
                rows = schedule.fixed_payment(after, rate, payment)
        except schedule.ScheduleError as exc:
            raise InvalidScheduleError(str(exc))

    last_due = open_[-1].commitment.due_date if open_ else commitments_service.add_months(debt.first_due_date, debt.installments - 1)
    planned: list[PlannedInstallment] = []
    for index, row in enumerate(rows):
        if index < len(open_):
            due = open_[index].commitment.due_date
        else:
            due = commitments_service.add_months(last_due, index - len(open_) + 1)
        planned.append(PlannedInstallment(row.number, due, row.principal, row.interest, row.payment, row.balance))

    plan = AmortizationPlan(
        outstanding_before=outstanding,
        outstanding_after=after,
        rows=planned,
        charges_before=sum((v.charges for v in open_), ZERO),
        charges_after=sum((p.charges for p in planned), ZERO),
        installments_before=len(open_),
    )
    return plan, open_


def preview_amortization(
    db: Session, user_id: uuid.UUID, debt_id: uuid.UUID, amount: Decimal | None, mode: str, today: date | None = None
) -> AmortizationPlan:
    today = today or date.today()
    debt = _get_debt(db, user_id, debt_id)
    plan, _ = _plan(db, user_id, debt, amount or ZERO, mode, today)
    return plan


def amortize(
    db: Session,
    user_id: uuid.UUID,
    debt_id: uuid.UUID,
    amount: Decimal | None,
    mode: str,
    paid_at: date | None,
    from_account_id: uuid.UUID | None,
    today: date | None = None,
) -> DebtDetail:
    """RF-038/RF-040: transfere o principal extra, cancela as parcelas em aberto e as regera
    pelo mesmo sistema e taxa (RB-027). Tudo na mesma transação."""
    today = today or date.today()
    debt = _get_debt(db, user_id, debt_id)
    plan, open_ = _plan(db, user_id, debt, amount or ZERO, mode, today)
    paid_at = paid_at or today
    if paid_at > today:
        raise FutureDateError(paid_at)

    source_id = from_account_id or debt.payment_account_id
    if source_id is None:
        raise AccountRequiredError(debt_id)
    _check_account(db, user_id, source_id)

    extra = plan.outstanding_before - plan.outstanding_after
    account = accounts_service.get_account(db, user_id, debt.account_id)
    try:
        transfer = transfers_service.create_transfer(
            db,
            user_id,
            from_account_id=source_id,
            to_account_id=debt.account_id,
            amount=extra,
            occurred_at=paid_at,
            description=f"Amortizacao: {account.name}"[:255],
            commit=False,
            today=today,
        )
    except transfers_service.FutureDateError:
        raise FutureDateError(paid_at)

    start_number = min((v.installment.number for v in open_), default=debt.installments + 1)
    for item in open_:
        commitments_service.cancel_commitment(
            db, user_id, item.commitment.id, today=today, via_debt=True, commit=False
        )
        item.installment.is_superseded = True

    total = start_number - 1 + len(plan.rows)
    _create_installments(db, user_id, debt, account.name, plan.rows, start_number, total, today)
    repository.add(
        db,
        DebtAmortization(
            user_id=user_id, debt_id=debt.id, transfer_id=transfer.id, amount=extra, paid_at=paid_at, mode=mode
        ),
    )
    db.commit()
    return get_debt(db, user_id, debt.id, today)


# ---------- leitura para outras slices (assets, reports) ----------

def debt_exists(db: Session, user_id: uuid.UUID, debt_id: uuid.UUID) -> bool:
    return repository.get_debt(db, debt_id, user_id) is not None


def debt_account_ids(db: Session, user_id: uuid.UUID) -> dict[uuid.UUID, uuid.UUID]:
    """debt_id -> id da conta `loan` (o saldo devedor é o negativo do saldo dessa conta)."""
    return {debt.id: debt.account_id for debt in repository.list_debts(db, user_id)}


def short_term_principal(
    db: Session, user_id: uuid.UUID, today: date | None = None, months: int = 12
) -> dict[uuid.UUID, Decimal]:
    """Principal das parcelas em aberto que vencem em até `months` meses, por conta da dívida (RF-044).

    Limitado ao saldo devedor: o curto prazo nunca passa do total da dívida.
    """
    today = today or date.today()
    horizon = commitments_service.add_months(today, months)
    result: dict[uuid.UUID, Decimal] = {}
    for debt in repository.list_debts(db, user_id):
        account = accounts_service.get_account(db, user_id, debt.account_id)
        outstanding = _outstanding(db, user_id, debt, account)
        due = sum(
            (
                view.installment.principal_part
                for view in _installment_views(db, user_id, debt, today)
                if view.status in ("open", "due_today", "overdue") and view.commitment.due_date <= horizon
            ),
            ZERO,
        )
        result[debt.account_id] = min(due, outstanding)
    return result
