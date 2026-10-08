"""create commitments and commitment_settlements tables

Revision ID: d4a7c2e91b36
Revises: c3e8b1f05a92
Create Date: 2026-10-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4a7c2e91b36'
down_revision: Union[str, Sequence[str], None] = 'c3e8b1f05a92'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('commitments',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('direction', sa.Enum('PAYABLE', 'RECEIVABLE', name='commitment_direction'), nullable=False),
    sa.Column('description', sa.String(length=255), nullable=False),
    sa.Column('counterparty', sa.String(length=255), nullable=True),
    sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('due_date', sa.Date(), nullable=False),
    sa.Column('category_id', sa.Uuid(), nullable=False),
    sa.Column('account_id', sa.Uuid(), nullable=True),
    sa.Column('notes', sa.String(length=1000), nullable=True),
    sa.Column('installment_group_id', sa.Uuid(), nullable=True),
    sa.Column('installment_number', sa.SmallInteger(), nullable=True),
    sa.Column('installment_count', sa.SmallInteger(), nullable=True),
    sa.Column('is_canceled', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], name='fk_commitments_account_id_accounts', ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['category_id'], ['categories.id'], name='fk_commitments_category_id_categories', ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_commitments_user_id_users', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_commitments_account_id'), 'commitments', ['account_id'], unique=False)
    op.create_index(op.f('ix_commitments_category_id'), 'commitments', ['category_id'], unique=False)
    op.create_index(op.f('ix_commitments_due_date'), 'commitments', ['due_date'], unique=False)
    op.create_index(op.f('ix_commitments_installment_group_id'), 'commitments', ['installment_group_id'], unique=False)
    op.create_index(op.f('ix_commitments_user_id'), 'commitments', ['user_id'], unique=False)

    op.create_table('commitment_settlements',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('commitment_id', sa.Uuid(), nullable=False),
    sa.Column('transaction_id', sa.Uuid(), nullable=False),
    sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('paid_at', sa.Date(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['commitment_id'], ['commitments.id'], name='fk_commitment_settlements_commitment_id_commitments', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], name='fk_commitment_settlements_transaction_id_transactions', ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_commitment_settlements_user_id_users', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('transaction_id', name='uq_commitment_settlements_transaction_id')
    )
    op.create_index(op.f('ix_commitment_settlements_commitment_id'), 'commitment_settlements', ['commitment_id'], unique=False)
    op.create_index(op.f('ix_commitment_settlements_user_id'), 'commitment_settlements', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_commitment_settlements_user_id'), table_name='commitment_settlements')
    op.drop_index(op.f('ix_commitment_settlements_commitment_id'), table_name='commitment_settlements')
    op.drop_table('commitment_settlements')
    op.drop_index(op.f('ix_commitments_user_id'), table_name='commitments')
    op.drop_index(op.f('ix_commitments_installment_group_id'), table_name='commitments')
    op.drop_index(op.f('ix_commitments_due_date'), table_name='commitments')
    op.drop_index(op.f('ix_commitments_category_id'), table_name='commitments')
    op.drop_index(op.f('ix_commitments_account_id'), table_name='commitments')
    op.drop_table('commitments')
    # create_table criou o enum junto; o drop_table não o remove sozinho no Postgres.
    sa.Enum(name='commitment_direction').drop(op.get_bind(), checkfirst=True)
