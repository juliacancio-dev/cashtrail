import calendar
import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from src.features.categories import service as categories_service
from src.features.transactions import service as transactions_service
from src.features.transactions.models import TransactionType


def default_period(today: date | None = None) -> tuple[date, date]:
    today = today or date.today()
    start = today.replace(day=1)
    last_day = calendar.monthrange(today.year, today.month)[1]
    end = today.replace(day=last_day)
    return start, end


def build_dashboard(db: Session, user_id: uuid.UUID, start_date: date, end_date: date) -> dict:
    """Agregação de leitura pura: consome transactions.service e categories.service,
    nunca acessa o repository/model de outra slice (09-vertical-slices.md).
    """
    transactions = transactions_service.list_transactions(db, user_id, start_date, end_date)
    category_names = {c.id: c.name for c in categories_service.list_categories(db, user_id)}

    income_total = Decimal("0")
    expense_total = Decimal("0")
    category_totals: dict[uuid.UUID, Decimal] = {}
    running_balance = Decimal("0")
    balance_evolution: list[tuple[date, Decimal]] = []

    for transaction in transactions:
        if transaction.type == TransactionType.INCOME:
            income_total += transaction.amount
            running_balance += transaction.amount
        else:
            expense_total += transaction.amount
            running_balance -= transaction.amount
            category_totals[transaction.category_id] = (
                category_totals.get(transaction.category_id, Decimal("0")) + transaction.amount
            )
        balance_evolution.append((transaction.occurred_at, running_balance))

    by_category = [
        (category_id, category_names.get(category_id, ""), total)
        for category_id, total in category_totals.items()
    ]

    return {
        "income_total": income_total,
        "expense_total": expense_total,
        "balance": income_total - expense_total,
        "by_category": by_category,
        "balance_evolution": balance_evolution,
    }
