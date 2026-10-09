"""accounts.opening_balance and categories.dre_group

Revision ID: b8e3a6c5d1f7
Revises: a7d2f5b84e69
Create Date: 2026-10-09 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b8e3a6c5d1f7'
down_revision: Union[str, Sequence[str], None] = 'a7d2f5b84e69'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DRE_GROUPS = (
    'revenue', 'deduction', 'variable_expense', 'fixed_expense', 'financial_expense', 'financial_revenue'
)


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'accounts',
        sa.Column('opening_balance', sa.Numeric(precision=12, scale=2), server_default=sa.text('0'), nullable=False),
    )
    op.add_column('categories', sa.Column('dre_group', sa.String(length=30), nullable=True))
    op.create_check_constraint(
        'ck_categories_dre_group',
        'categories',
        "dre_group IS NULL OR dre_group IN (" + ", ".join(f"'{g}'" for g in DRE_GROUPS) + ")",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('ck_categories_dre_group', 'categories', type_='check')
    op.drop_column('categories', 'dre_group')
    op.drop_column('accounts', 'opening_balance')
