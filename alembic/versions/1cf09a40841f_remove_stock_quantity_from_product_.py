"""remove_stock_quantity_from_product_variants

Revision ID: 1cf09a40841f
Revises: 42d6c7c9a958
Create Date: 2025-11-02 18:44:20.874424

IMPORTANT MIGRATION:
This migration removes stock_quantity from product_variants table.
Stock management is now exclusively handled via the inventory table.

Changes:
- Removes stock_quantity column from product_variants
- Adds UNIQUE constraint to sku column (if not exists)
- Data migration: Any existing variant stock data will be lost
  (You should manually migrate to inventory table before running this)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


# revision identifiers, used by Alembic.
revision = '1cf09a40841f'
down_revision = '42d6c7c9a958'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Remove stock_quantity from product_variants and add unique constraint to sku.
    
    WARNING: This will drop the stock_quantity column and any data in it.
    If you have existing variant stock data, migrate it to the inventory table first!
    """
    # Check database type
    conn = op.get_bind()
    dialect_name = conn.dialect.name
    
    # Remove stock_quantity column
    with op.batch_alter_table('product_variants', schema=None) as batch_op:
        batch_op.drop_column('stock_quantity')
    
    # Add unique constraint to sku if using MySQL/PostgreSQL
    if dialect_name in ('mysql', 'postgresql'):
        try:
            with op.batch_alter_table('product_variants', schema=None) as batch_op:
                batch_op.create_unique_constraint('uq_product_variants_sku', ['sku'])
        except Exception:
            # Constraint might already exist or there might be duplicate SKUs
            pass


def downgrade() -> None:
    """
    Restore stock_quantity column to product_variants.
    
    NOTE: Data will be lost - this only restores the schema structure.
    """
    # Remove unique constraint from sku
    conn = op.get_bind()
    dialect_name = conn.dialect.name
    
    if dialect_name in ('mysql', 'postgresql'):
        try:
            with op.batch_alter_table('product_variants', schema=None) as batch_op:
                batch_op.drop_constraint('uq_product_variants_sku', type_='unique')
        except Exception:
            pass
    
    # Add back stock_quantity column with default value 0
    with op.batch_alter_table('product_variants', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('stock_quantity', sa.Integer(), nullable=False, server_default='0')
        )
