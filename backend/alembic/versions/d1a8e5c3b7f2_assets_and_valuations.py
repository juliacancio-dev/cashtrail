"""assets and asset valuations

Revision ID: d1a8e5c3b7f2
Revises: c9f4b7a2e6d1
Create Date: 2026-10-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1a8e5c3b7f2'
down_revision: Union[str, Sequence[str], None] = 'c9f4b7a2e6d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'assets',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('kind', sa.String(length=20), nullable=False),
        sa.Column('acquired_at', sa.Date(), nullable=True),
        sa.Column('acquisition_value', sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column('debt_id', sa.Uuid(), nullable=True),
        sa.Column('disposed_at', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("kind IN ('real_estate', 'vehicle', 'other')", name='ck_assets_kind'),
        sa.CheckConstraint(
            'acquisition_value IS NULL OR acquisition_value >= 0', name='ck_assets_acquisition_value'
        ),
        sa.ForeignKeyConstraint(['debt_id'], ['debts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('debt_id'),
    )
    op.create_index(op.f('ix_assets_user_id'), 'assets', ['user_id'], unique=False)

    op.create_table(
        'asset_valuations',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('asset_id', sa.Uuid(), nullable=False),
        sa.Column('valued_at', sa.Date(), nullable=False),
        sa.Column('value', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('note', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('value >= 0', name='ck_asset_valuations_value'),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('asset_id', 'valued_at', name='uq_asset_valuations_asset_id_valued_at'),
    )
    op.create_index(op.f('ix_asset_valuations_user_id'), 'asset_valuations', ['user_id'], unique=False)
    op.create_index(op.f('ix_asset_valuations_asset_id'), 'asset_valuations', ['asset_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_asset_valuations_asset_id'), table_name='asset_valuations')
    op.drop_index(op.f('ix_asset_valuations_user_id'), table_name='asset_valuations')
    op.drop_table('asset_valuations')
    op.drop_index(op.f('ix_assets_user_id'), table_name='assets')
    op.drop_table('assets')
