"""add_is_active_to_users

Revision ID: 004
Revises: 003
Create Date: 2024-12-08 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add is_active column to users table
    op.add_column('users', sa.Column('is_active', sa.Boolean(), nullable=False, default=True, comment='계정 활성화 상태'))


def downgrade() -> None:
    # Remove is_active column from users table
    op.drop_column('users', 'is_active')