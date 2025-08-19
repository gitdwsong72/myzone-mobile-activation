"""add_password_hash_to_users

Revision ID: 003
Revises: 002
Create Date: 2024-12-08 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add password_hash column to users table
    op.add_column('users', sa.Column('password_hash', sa.String(length=255), nullable=True, comment='해시된 비밀번호'))


def downgrade() -> None:
    # Remove password_hash column from users table
    op.drop_column('users', 'password_hash')