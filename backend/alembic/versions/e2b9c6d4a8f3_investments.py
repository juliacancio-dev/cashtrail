"""investments: assets, operations, quotes, request log

Revision ID: e2b9c6d4a8f3
Revises: d1a8e5c3b7f2
Create Date: 2026-10-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e2b9c6d4a8f3'
down_revision: Union[str, Sequence[str], None] = 'd1a8e5c3b7f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # O SQLAlchemy grava o NOME do membro do enum (LOAN, não loan), então o valor é INVESTMENT.
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE account_type ADD VALUE IF NOT EXISTS 'INVESTMENT'")

    op.create_table(
        'investment_assets',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('account_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=True),
        sa.Column('asset_class', sa.String(length=20), nullable=False),
        sa.Column('quote_source', sa.String(length=10), nullable=False),
        sa.Column('is_archived', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint(
            "asset_class IN ('stock', 'fii', 'etf', 'bdr', 'fixed_income', 'treasury', 'fund', 'crypto', 'other')",
            name='ck_investment_assets_asset_class',
        ),
        sa.CheckConstraint("quote_source IN ('brapi', 'manual')", name='ck_investment_assets_quote_source'),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'account_id', 'symbol', name='uq_investment_assets_user_account_symbol'),
    )
    op.create_index(op.f('ix_investment_assets_user_id'), 'investment_assets', ['user_id'], unique=False)
    op.create_index(op.f('ix_investment_assets_account_id'), 'investment_assets', ['account_id'], unique=False)

    op.create_table(
        'investment_operations',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('asset_id', sa.Uuid(), nullable=False),
        sa.Column('kind', sa.String(length=10), nullable=False),
        sa.Column('occurred_at', sa.Date(), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column('unit_price', sa.Numeric(precision=14, scale=6), nullable=False),
        sa.Column('fees', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('amount', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('cost_basis', sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column('gain', sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column('cash_account_id', sa.Uuid(), nullable=True),
        sa.Column('category_id', sa.Uuid(), nullable=True),
        sa.Column('transfer_id', sa.Uuid(), nullable=True),
        sa.Column('transaction_id', sa.Uuid(), nullable=True),
        sa.Column('note', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("kind IN ('buy', 'sell', 'income', 'adjust')", name='ck_investment_operations_kind'),
        sa.ForeignKeyConstraint(['asset_id'], ['investment_assets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['cash_account_id'], ['accounts.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['transfer_id'], ['transfers.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('transfer_id'),
        sa.UniqueConstraint('transaction_id'),
    )
    op.create_index(op.f('ix_investment_operations_user_id'), 'investment_operations', ['user_id'], unique=False)
    op.create_index(
        'ix_investment_operations_asset_id_occurred_at',
        'investment_operations',
        ['asset_id', 'occurred_at'],
        unique=False,
    )

    op.create_table(
        'investment_quotes',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('asset_id', sa.Uuid(), nullable=False),
        sa.Column('quoted_on', sa.Date(), nullable=False),
        sa.Column('price', sa.Numeric(precision=14, scale=6), nullable=False),
        sa.Column('source', sa.String(length=10), nullable=False),
        sa.Column('fetched_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('price >= 0', name='ck_investment_quotes_price'),
        sa.ForeignKeyConstraint(['asset_id'], ['investment_assets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('asset_id', 'quoted_on', name='uq_investment_quotes_asset_id_quoted_on'),
    )
    op.create_index(op.f('ix_investment_quotes_user_id'), 'investment_quotes', ['user_id'], unique=False)
    op.create_index(op.f('ix_investment_quotes_asset_id'), 'investment_quotes', ['asset_id'], unique=False)

    op.create_table(
        'quote_request_log',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('requested_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('provider', sa.String(length=20), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('ok', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_quote_request_log_requested_at'), 'quote_request_log', ['requested_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema. O valor INVESTMENT do enum account_type não é removido (Postgres não suporta com segurança)."""
    op.drop_index(op.f('ix_quote_request_log_requested_at'), table_name='quote_request_log')
    op.drop_table('quote_request_log')
    op.drop_index(op.f('ix_investment_quotes_asset_id'), table_name='investment_quotes')
    op.drop_index(op.f('ix_investment_quotes_user_id'), table_name='investment_quotes')
    op.drop_table('investment_quotes')
    op.drop_index('ix_investment_operations_asset_id_occurred_at', table_name='investment_operations')
    op.drop_index(op.f('ix_investment_operations_user_id'), table_name='investment_operations')
    op.drop_table('investment_operations')
    op.drop_index(op.f('ix_investment_assets_account_id'), table_name='investment_assets')
    op.drop_index(op.f('ix_investment_assets_user_id'), table_name='investment_assets')
    op.drop_table('investment_assets')
