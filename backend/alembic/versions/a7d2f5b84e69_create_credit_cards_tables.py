"""create credit_cards, card_purchases and card_invoice_payments tables

Revision ID: a7d2f5b84e69
Revises: f6c9e4a13d58
Create Date: 2026-10-09 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7d2f5b84e69'
down_revision: Union[str, Sequence[str], None] = 'f6c9e4a13d58'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('credit_cards',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('account_id', sa.Uuid(), nullable=False),
    sa.Column('closing_day', sa.SmallInteger(), nullable=False),
    sa.Column('due_day', sa.SmallInteger(), nullable=False),
    sa.Column('credit_limit', sa.Numeric(precision=12, scale=2), nullable=True),
    sa.Column('default_payment_account_id', sa.Uuid(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('closing_day BETWEEN 1 AND 31', name='ck_credit_cards_closing_day'),
    sa.CheckConstraint('due_day BETWEEN 1 AND 31', name='ck_credit_cards_due_day'),
    sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], name='fk_credit_cards_account_id_accounts', ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['default_payment_account_id'], ['accounts.id'], name='fk_credit_cards_default_payment_account_id_accounts', ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_credit_cards_user_id_users', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('account_id', name='uq_credit_cards_account_id')
    )
    op.create_index(op.f('ix_credit_cards_user_id'), 'credit_cards', ['user_id'], unique=False)

    op.create_table('card_purchases',
    sa.Column('transaction_id', sa.Uuid(), nullable=False),
    sa.Column('credit_card_id', sa.Uuid(), nullable=False),
    sa.Column('invoice_closing_date', sa.Date(), nullable=False),
    sa.ForeignKeyConstraint(['credit_card_id'], ['credit_cards.id'], name='fk_card_purchases_credit_card_id_credit_cards', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], name='fk_card_purchases_transaction_id_transactions', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('transaction_id')
    )
    op.create_index('ix_card_purchases_credit_card_id_closing', 'card_purchases', ['credit_card_id', 'invoice_closing_date'], unique=False)

    op.create_table('card_invoice_payments',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('credit_card_id', sa.Uuid(), nullable=False),
    sa.Column('invoice_closing_date', sa.Date(), nullable=False),
    sa.Column('transfer_id', sa.Uuid(), nullable=False),
    sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('paid_at', sa.Date(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['credit_card_id'], ['credit_cards.id'], name='fk_card_invoice_payments_credit_card_id_credit_cards', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['transfer_id'], ['transfers.id'], name='fk_card_invoice_payments_transfer_id_transfers', ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_card_invoice_payments_user_id_users', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('transfer_id', name='uq_card_invoice_payments_transfer_id')
    )
    op.create_index(op.f('ix_card_invoice_payments_credit_card_id'), 'card_invoice_payments', ['credit_card_id'], unique=False)
    op.create_index(op.f('ix_card_invoice_payments_user_id'), 'card_invoice_payments', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_card_invoice_payments_user_id'), table_name='card_invoice_payments')
    op.drop_index(op.f('ix_card_invoice_payments_credit_card_id'), table_name='card_invoice_payments')
    op.drop_table('card_invoice_payments')
    op.drop_index('ix_card_purchases_credit_card_id_closing', table_name='card_purchases')
    op.drop_table('card_purchases')
    op.drop_index(op.f('ix_credit_cards_user_id'), table_name='credit_cards')
    op.drop_table('credit_cards')
