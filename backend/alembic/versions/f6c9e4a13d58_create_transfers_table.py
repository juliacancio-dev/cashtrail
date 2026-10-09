"""create transfers table

Revision ID: f6c9e4a13d58
Revises: e5b8d3f02c47
Create Date: 2026-10-09 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f6c9e4a13d58'
down_revision: Union[str, Sequence[str], None] = 'e5b8d3f02c47'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('transfers',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('from_account_id', sa.Uuid(), nullable=False),
    sa.Column('to_account_id', sa.Uuid(), nullable=False),
    sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('occurred_at', sa.Date(), nullable=False),
    sa.Column('description', sa.String(length=255), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('from_account_id <> to_account_id', name='ck_transfers_different_accounts'),
    sa.CheckConstraint('amount > 0', name='ck_transfers_amount_positive'),
    sa.ForeignKeyConstraint(['from_account_id'], ['accounts.id'], name='fk_transfers_from_account_id_accounts', ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['to_account_id'], ['accounts.id'], name='fk_transfers_to_account_id_accounts', ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_transfers_user_id_users', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_transfers_from_account_id'), 'transfers', ['from_account_id'], unique=False)
    op.create_index(op.f('ix_transfers_to_account_id'), 'transfers', ['to_account_id'], unique=False)
    op.create_index(op.f('ix_transfers_user_id'), 'transfers', ['user_id'], unique=False)
    op.create_index('ix_transfers_user_id_occurred_at', 'transfers', ['user_id', 'occurred_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_transfers_user_id_occurred_at', table_name='transfers')
    op.drop_index(op.f('ix_transfers_user_id'), table_name='transfers')
    op.drop_index(op.f('ix_transfers_to_account_id'), table_name='transfers')
    op.drop_index(op.f('ix_transfers_from_account_id'), table_name='transfers')
    op.drop_table('transfers')
