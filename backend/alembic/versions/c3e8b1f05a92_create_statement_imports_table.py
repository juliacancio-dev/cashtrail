"""create statement_imports table

Revision ID: c3e8b1f05a92
Revises: a1c9e4d27f10
Create Date: 2026-10-06 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3e8b1f05a92'
down_revision: Union[str, Sequence[str], None] = 'a1c9e4d27f10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('statement_imports',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('account_id', sa.Uuid(), nullable=False),
    sa.Column('file_name', sa.String(length=255), nullable=False),
    sa.Column('file_sha256', sa.String(length=64), nullable=False),
    sa.Column('rows_total', sa.Integer(), nullable=False),
    sa.Column('transactions_created', sa.Integer(), nullable=False),
    sa.Column('rows_skipped', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(
        ['account_id'], ['accounts.id'], name='fk_statement_imports_account_id_accounts', ondelete='RESTRICT'
    ),
    sa.ForeignKeyConstraint(
        ['user_id'], ['users.id'], name='fk_statement_imports_user_id_users', ondelete='CASCADE'
    ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_statement_imports_account_id'), 'statement_imports', ['account_id'], unique=False)
    op.create_index(op.f('ix_statement_imports_file_sha256'), 'statement_imports', ['file_sha256'], unique=False)
    op.create_index(op.f('ix_statement_imports_user_id'), 'statement_imports', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_statement_imports_user_id'), table_name='statement_imports')
    op.drop_index(op.f('ix_statement_imports_file_sha256'), table_name='statement_imports')
    op.drop_index(op.f('ix_statement_imports_account_id'), table_name='statement_imports')
    op.drop_table('statement_imports')
