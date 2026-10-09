"""debts, loan accounts and split settlements

Revision ID: c9f4b7a2e6d1
Revises: b8e3a6c5d1f7
Create Date: 2026-10-09 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c9f4b7a2e6d1'
down_revision: Union[str, Sequence[str], None] = 'b8e3a6c5d1f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ADD VALUE não pode rodar dentro da transação do Alembic junto de outros comandos que usem o
    # valor novo (R-11.1). Aqui nada usa 'LOAN' na migração, mas fica em autocommit para ser seguro.
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE account_type ADD VALUE IF NOT EXISTS 'LOAN'")

    op.create_table(
        'debts',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('account_id', sa.Uuid(), nullable=False),
        sa.Column('creditor', sa.String(length=255), nullable=True),
        sa.Column('principal', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('contracted_at', sa.Date(), nullable=False),
        sa.Column('installments', sa.SmallInteger(), nullable=False),
        sa.Column('system', sa.String(length=10), nullable=False),
        sa.Column('monthly_rate', sa.Numeric(precision=7, scale=4), nullable=False),
        sa.Column('first_due_date', sa.Date(), nullable=False),
        sa.Column('payment_account_id', sa.Uuid(), nullable=True),
        sa.Column('interest_category_id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("system IN ('price', 'sac', 'zero')", name='ck_debts_system'),
        sa.CheckConstraint('principal > 0', name='ck_debts_principal'),
        sa.CheckConstraint('monthly_rate >= 0', name='ck_debts_monthly_rate'),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['interest_category_id'], ['categories.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['payment_account_id'], ['accounts.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('account_id'),
    )
    op.create_index(op.f('ix_debts_user_id'), 'debts', ['user_id'], unique=False)

    op.add_column('commitments', sa.Column('debt_id', sa.Uuid(), nullable=True))
    op.create_index(op.f('ix_commitments_debt_id'), 'commitments', ['debt_id'], unique=False)
    op.create_foreign_key(
        'commitments_debt_id_fkey', 'commitments', 'debts', ['debt_id'], ['id'], ondelete='SET NULL'
    )

    op.create_table(
        'debt_installments',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('debt_id', sa.Uuid(), nullable=False),
        sa.Column('number', sa.SmallInteger(), nullable=False),
        sa.Column('commitment_id', sa.Uuid(), nullable=False),
        sa.Column('principal_part', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('is_superseded', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['commitment_id'], ['commitments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['debt_id'], ['debts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('commitment_id'),
    )
    op.create_index(op.f('ix_debt_installments_user_id'), 'debt_installments', ['user_id'], unique=False)
    op.create_index('ix_debt_installments_debt_id_number', 'debt_installments', ['debt_id', 'number'], unique=False)

    op.create_table(
        'debt_amortizations',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('debt_id', sa.Uuid(), nullable=False),
        sa.Column('transfer_id', sa.Uuid(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('paid_at', sa.Date(), nullable=False),
        sa.Column('mode', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint(
            "mode IN ('reduce_term', 'reduce_installment', 'payoff')", name='ck_debt_amortizations_mode'
        ),
        sa.ForeignKeyConstraint(['debt_id'], ['debts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['transfer_id'], ['transfers.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('transfer_id'),
    )
    op.create_index(op.f('ix_debt_amortizations_user_id'), 'debt_amortizations', ['user_id'], unique=False)
    op.create_index(op.f('ix_debt_amortizations_debt_id'), 'debt_amortizations', ['debt_id'], unique=False)

    # Baixa de parcela de dívida: parte vira transferência (principal) e pode não haver despesa.
    op.alter_column('commitment_settlements', 'transaction_id', existing_type=sa.Uuid(), nullable=True)
    op.add_column('commitment_settlements', sa.Column('transfer_id', sa.Uuid(), nullable=True))
    op.create_unique_constraint(
        'commitment_settlements_transfer_id_key', 'commitment_settlements', ['transfer_id']
    )
    op.create_foreign_key(
        'commitment_settlements_transfer_id_fkey',
        'commitment_settlements',
        'transfers',
        ['transfer_id'],
        ['id'],
        ondelete='RESTRICT',
    )
    op.create_check_constraint(
        'ck_commitment_settlements_target',
        'commitment_settlements',
        'transaction_id IS NOT NULL OR transfer_id IS NOT NULL',
    )


def downgrade() -> None:
    """Downgrade schema.

    O valor 'LOAN' do enum account_type NÃO é removido (o Postgres não suporta remover valor de enum
    com segurança); ele fica sem uso. Baixas só-transferência (parcelas de dívida) são apagadas
    para poder devolver transaction_id a NOT NULL.
    """
    op.drop_constraint('ck_commitment_settlements_target', 'commitment_settlements', type_='check')
    op.execute('DELETE FROM commitment_settlements WHERE transaction_id IS NULL')
    op.drop_constraint('commitment_settlements_transfer_id_fkey', 'commitment_settlements', type_='foreignkey')
    op.drop_constraint('commitment_settlements_transfer_id_key', 'commitment_settlements', type_='unique')
    op.drop_column('commitment_settlements', 'transfer_id')
    op.alter_column('commitment_settlements', 'transaction_id', existing_type=sa.Uuid(), nullable=False)

    op.drop_index(op.f('ix_debt_amortizations_debt_id'), table_name='debt_amortizations')
    op.drop_index(op.f('ix_debt_amortizations_user_id'), table_name='debt_amortizations')
    op.drop_table('debt_amortizations')
    op.drop_index('ix_debt_installments_debt_id_number', table_name='debt_installments')
    op.drop_index(op.f('ix_debt_installments_user_id'), table_name='debt_installments')
    op.drop_table('debt_installments')

    op.drop_constraint('commitments_debt_id_fkey', 'commitments', type_='foreignkey')
    op.drop_index(op.f('ix_commitments_debt_id'), table_name='commitments')
    op.drop_column('commitments', 'debt_id')

    op.drop_index(op.f('ix_debts_user_id'), table_name='debts')
    op.drop_table('debts')
