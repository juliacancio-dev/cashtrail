"""tax: category ir_kind, year settings and income statements

Revision ID: f3c1d7a9b5e2
Revises: e2b9c6d4a8f3
Create Date: 2026-10-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f3c1d7a9b5e2'
down_revision: Union[str, Sequence[str], None] = 'e2b9c6d4a8f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

IR_KINDS = ('deduction_health', 'deduction_education', 'deduction_pension')


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('categories', sa.Column('ir_kind', sa.String(length=30), nullable=True))
    op.create_check_constraint(
        'ck_categories_ir_kind',
        'categories',
        "ir_kind IS NULL OR ir_kind IN (" + ", ".join(f"'{kind}'" for kind in IR_KINDS) + ")",
    )

    op.create_table(
        'tax_year_settings',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('year', sa.SmallInteger(), nullable=False),
        sa.Column('dependents_count', sa.SmallInteger(), nullable=False),
        sa.CheckConstraint('dependents_count >= 0 AND dependents_count <= 20', name='ck_tax_year_settings_dependents'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'year', name='uq_tax_year_settings_user_year'),
    )
    op.create_index(op.f('ix_tax_year_settings_user_id'), 'tax_year_settings', ['user_id'], unique=False)

    op.create_table(
        'tax_income_statements',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('year', sa.SmallInteger(), nullable=False),
        sa.Column('payer_name', sa.String(length=120), nullable=False),
        sa.Column('kind', sa.String(length=20), nullable=False),
        sa.Column('gross_income', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('social_security', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('withheld_tax', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('note', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint(
            "kind IN ('salary', 'other_taxable', 'thirteenth', 'plr', 'exclusive_other', 'exempt')",
            name='ck_tax_income_statements_kind',
        ),
        sa.CheckConstraint(
            'gross_income >= 0 AND social_security >= 0 AND withheld_tax >= 0',
            name='ck_tax_income_statements_amounts',
        ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_tax_income_statements_user_id'), 'tax_income_statements', ['user_id'], unique=False)
    op.create_index(op.f('ix_tax_income_statements_year'), 'tax_income_statements', ['year'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_tax_income_statements_year'), table_name='tax_income_statements')
    op.drop_index(op.f('ix_tax_income_statements_user_id'), table_name='tax_income_statements')
    op.drop_table('tax_income_statements')
    op.drop_index(op.f('ix_tax_year_settings_user_id'), table_name='tax_year_settings')
    op.drop_table('tax_year_settings')
    op.drop_constraint('ck_categories_ir_kind', 'categories', type_='check')
    op.drop_column('categories', 'ir_kind')
