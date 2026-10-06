"""create password_reset_tokens table, add password_changed_at to users

Revision ID: a1c9e4d27f10
Revises: 5794659919a8
Create Date: 2026-09-28 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1c9e4d27f10'
down_revision: Union[str, Sequence[str], None] = '5794659919a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('password_changed_at', sa.DateTime(timezone=True), nullable=True))
    op.create_table('password_reset_tokens',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('token_hash', sa.String(length=64), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(
        ['user_id'], ['users.id'], name='fk_password_reset_tokens_user_id_users', ondelete='CASCADE'
    ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('token_hash', name='uq_password_reset_tokens_token_hash')
    )
    op.create_index(op.f('ix_password_reset_tokens_user_id'), 'password_reset_tokens', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_password_reset_tokens_user_id'), table_name='password_reset_tokens')
    op.drop_table('password_reset_tokens')
    op.drop_column('users', 'password_changed_at')
