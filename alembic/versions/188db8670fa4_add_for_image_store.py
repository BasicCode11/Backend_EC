"""add for image store

Revision ID: 188db8670fa4
Revises: 3fe71e54b8e1
Create Date: 2025-11-27 15:46:46.682557

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '188db8670fa4'
down_revision = '3fe71e54b8e1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add Cloudinary public_id columns to product assets."""
    op.add_column('product_images', sa.Column('image_public_id', sa.String(length=255), nullable=True))
    op.add_column('product_variants', sa.Column('image_public_id', sa.String(length=255), nullable=True))


def downgrade() -> None:
    """Remove Cloudinary public_id columns from product assets."""
    op.drop_column('product_variants', 'image_public_id')
    op.drop_column('product_images', 'image_public_id')
