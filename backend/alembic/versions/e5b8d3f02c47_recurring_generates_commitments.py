"""recurring can generate commitments

Revision ID: e5b8d3f02c47
Revises: d4a7c2e91b36
Create Date: 2026-10-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5b8d3f02c47'
down_revision: Union[str, Sequence[str], None] = 'd4a7c2e91b36'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'recurring_transactions',
        sa.Column('generate_as_commitment', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    )
    op.add_column('commitments', sa.Column('recurring_transaction_id', sa.Uuid(), nullable=True))
    op.create_index(
        op.f('ix_commitments_recurring_transaction_id'), 'commitments', ['recurring_transaction_id'], unique=False
    )
    op.create_foreign_key(
        'fk_commitments_recurring_transaction_id_recurring_transactions',
        'commitments', 'recurring_transactions', ['recurring_transaction_id'], ['id'], ondelete='SET NULL'
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        'fk_commitments_recurring_transaction_id_recurring_transactions', 'commitments', type_='foreignkey'
    )
    op.drop_index(op.f('ix_commitments_recurring_transaction_id'), table_name='commitments')
    op.drop_column('commitments', 'recurring_transaction_id')
    op.drop_column('recurring_transactions', 'generate_as_commitment')
