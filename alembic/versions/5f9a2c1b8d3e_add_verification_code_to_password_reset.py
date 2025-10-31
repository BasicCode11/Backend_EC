"""add verification code to password reset

Revision ID: 5f9a2c1b8d3e
Revises: 48d83cf3298a
Create Date: 2025-10-30 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5f9a2c1b8d3e'
down_revision: Union[str, None] = '48d83cf3298a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns to password_reset_tokens table
    op.add_column('password_reset_tokens', 
        sa.Column('verification_code', sa.String(length=6), nullable=True)
    )
    op.add_column('password_reset_tokens', 
        sa.Column('code_verified', sa.Boolean(), nullable=True, server_default='0')
    )
    
    # Create index on verification_code for faster lookups
    op.create_index('ix_password_reset_tokens_verification_code', 
                    'password_reset_tokens', 
                    ['verification_code'], 
                    unique=False)
    
    # Update existing rows to have a default verification code (they won't be used anyway since they're old)
    op.execute("UPDATE password_reset_tokens SET verification_code = '000000' WHERE verification_code IS NULL")
    op.execute("UPDATE password_reset_tokens SET code_verified = 0 WHERE code_verified IS NULL")
    
    # Now make the columns non-nullable (must specify existing_type for MySQL)
    op.alter_column('password_reset_tokens', 'verification_code', 
                   existing_type=sa.String(length=6),
                   nullable=False)
    op.alter_column('password_reset_tokens', 'code_verified', 
                   existing_type=sa.Boolean(),
                   nullable=False)


def downgrade() -> None:
    # Drop index
    op.drop_index('ix_password_reset_tokens_verification_code', table_name='password_reset_tokens')
    
    # Drop columns
    op.drop_column('password_reset_tokens', 'code_verified')
    op.drop_column('password_reset_tokens', 'verification_code')
