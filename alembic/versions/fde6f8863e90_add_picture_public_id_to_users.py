"""add_picture_public_id_to_users

Revision ID: fde6f8863e90
Revises: 1cf09a40841f
Create Date: 2025-11-16 18:25:01.950466

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fde6f8863e90'
down_revision = '1cf09a40841f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add picture_public_id column to users table
    op.add_column('users', sa.Column('picture_public_id', sa.String(length=255), nullable=True))


def downgrade() -> None:
    # Remove picture_public_id column from users table
    op.drop_column('users', 'picture_public_id')
