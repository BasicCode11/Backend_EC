"""create_user_addresses_table

Revision ID: be037b5ef6d1
Revises: 2e0e9d9d9174
Create Date: 2025-10-28 16:37:24.358293

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'be037b5ef6d1'
down_revision = '2e0e9d9d9174'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if table exists and alter columns if needed
    # This handles the case where the table was created outside migrations
    
    # For existing installations: Alter the coordinate columns to ensure proper precision
    # DECIMAL(10, 7) allows values from -999.9999999 to 999.9999999
    # This is sufficient for both longitude (-180 to 180) and latitude (-90 to 90)
    
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    if 'user_addresses' in inspector.get_table_names():
        # Table exists, alter the columns if they have wrong precision
        op.alter_column('user_addresses', 'longitude',
                       existing_type=sa.DECIMAL(precision=10, scale=7),
                       type_=sa.DECIMAL(precision=10, scale=7),
                       existing_nullable=True)
        
        op.alter_column('user_addresses', 'latitude',
                       existing_type=sa.DECIMAL(precision=10, scale=7),
                       type_=sa.DECIMAL(precision=10, scale=7),
                       existing_nullable=True)


def downgrade() -> None:
    # No downgrade needed
    pass
