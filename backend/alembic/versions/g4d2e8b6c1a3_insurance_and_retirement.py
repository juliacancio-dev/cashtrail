"""insurance policies and retirement plans

Revision ID: g4d2e8b6c1a3
Revises: f3c1d7a9b5e2
Create Date: 2026-10-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'g4d2e8b6c1a3'
down_revision: Union[str, Sequence[str], None] = 'f3c1d7a9b5e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'insurance_policies',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('kind', sa.String(length=10), nullable=False),
        sa.Column('insurer', sa.String(length=120), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('premium_amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('premium_frequency', sa.String(length=10), nullable=False),
        sa.Column('coverage_amount', sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column('starts_on', sa.Date(), nullable=True),
        sa.Column('renews_on', sa.Date(), nullable=False),
        sa.Column('first_due_on', sa.Date(), nullable=True),
        sa.Column('asset_id', sa.Uuid(), nullable=True),
        sa.Column('payment_account_id', sa.Uuid(), nullable=False),
        sa.Column('category_id', sa.Uuid(), nullable=False),
        sa.Column('recurring_id', sa.Uuid(), nullable=True),
        sa.Column('commitment_id', sa.Uuid(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('notes', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("kind IN ('life', 'health', 'auto', 'home', 'travel', 'other')", name='ck_insurance_policies_kind'),
        sa.CheckConstraint("premium_frequency IN ('monthly', 'annual')", name='ck_insurance_policies_frequency'),
        sa.CheckConstraint('premium_amount > 0', name='ck_insurance_policies_premium'),
        sa.CheckConstraint('coverage_amount IS NULL OR coverage_amount >= 0', name='ck_insurance_policies_coverage'),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['commitment_id'], ['commitments.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['payment_account_id'], ['accounts.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['recurring_id'], ['recurring_transactions.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_insurance_policies_user_id'), 'insurance_policies', ['user_id'], unique=False)
    op.create_index(op.f('ix_insurance_policies_asset_id'), 'insurance_policies', ['asset_id'], unique=False)

    op.create_table(
        'retirement_plans',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('current_age', sa.SmallInteger(), nullable=False),
        sa.Column('target_age', sa.SmallInteger(), nullable=False),
        sa.Column('monthly_income_wanted', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('public_benefit_monthly', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('real_return_annual', sa.Numeric(precision=6, scale=4), nullable=False),
        sa.Column('withdrawal_rate', sa.Numeric(precision=6, scale=4), nullable=False),
        sa.Column('monthly_contribution', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('include_assets', sa.Boolean(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('current_age >= 0 AND current_age <= 120', name='ck_retirement_plans_current_age'),
        sa.CheckConstraint('target_age > current_age AND target_age <= 120', name='ck_retirement_plans_target_age'),
        sa.CheckConstraint('monthly_income_wanted > 0', name='ck_retirement_plans_income'),
        sa.CheckConstraint('withdrawal_rate > 0 AND withdrawal_rate <= 0.2', name='ck_retirement_plans_withdrawal'),
        sa.CheckConstraint('real_return_annual >= -0.2 AND real_return_annual <= 0.3', name='ck_retirement_plans_return'),
        sa.CheckConstraint('monthly_contribution >= 0', name='ck_retirement_plans_contribution'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('retirement_plans')
    op.drop_index(op.f('ix_insurance_policies_asset_id'), table_name='insurance_policies')
    op.drop_index(op.f('ix_insurance_policies_user_id'), table_name='insurance_policies')
    op.drop_table('insurance_policies')
