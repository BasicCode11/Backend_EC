"""new changes

Revision ID: 4af86049bdf7
Revises: 0b3ceed6b9f3
Create Date: 2025-11-27 11:05:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '4af86049bdf7'
down_revision = '0b3ceed6b9f3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop foreign keys first
    op.drop_constraint('email_verification_tokens_ibfk_1', 'email_verification_tokens', type_='foreignkey')
    op.drop_constraint('password_reset_tokens_ibfk_1', 'password_reset_tokens', type_='foreignkey')

    # Drop tables (indexes are dropped automatically)
    op.drop_table('email_verification_tokens')
    op.drop_table('password_reset_tokens')
    op.drop_table('token_blacklist')  # This table has no FK, safe to drop directly

    # Add new column
    op.add_column('categories', sa.Column('image_public_id', sa.String(length=255), nullable=True))


def downgrade() -> None:
    # Remove new column
    op.drop_column('categories', 'image_public_id')

    # Recreate dropped tables
    op.create_table(
        'email_verification_tokens',
        sa.Column('id', mysql.INTEGER(), autoincrement=True, nullable=False),
        sa.Column('user_id', mysql.INTEGER(), nullable=False),
        sa.Column('token', mysql.VARCHAR(length=255), nullable=False),
        sa.Column('expires_at', mysql.DATETIME(), nullable=False),
        sa.Column('used', mysql.TINYINT(display_width=1), nullable=False),
        sa.Column('created_at', mysql.DATETIME(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='email_verification_tokens_ibfk_1', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_collate='utf8mb4_0900_ai_ci',
        mysql_default_charset='utf8mb4',
        mysql_engine='InnoDB'
    )
    op.create_index('ix_email_verification_tokens_user_id', 'email_verification_tokens', ['user_id'], unique=False)
    op.create_index('ix_email_verification_tokens_token', 'email_verification_tokens', ['token'], unique=False)
    op.create_index('ix_email_verification_tokens_id', 'email_verification_tokens', ['id'], unique=False)

    op.create_table(
        'password_reset_tokens',
        sa.Column('id', mysql.INTEGER(), autoincrement=True, nullable=False),
        sa.Column('user_id', mysql.INTEGER(), nullable=False),
        sa.Column('token', mysql.VARCHAR(length=255), nullable=False),
        sa.Column('verification_code', mysql.VARCHAR(length=6), nullable=False),
        sa.Column('code_verified', mysql.TINYINT(display_width=1), nullable=False),
        sa.Column('expires_at', mysql.DATETIME(), nullable=False),
        sa.Column('used', mysql.TINYINT(display_width=1), nullable=False),
        sa.Column('created_at', mysql.DATETIME(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='password_reset_tokens_ibfk_1', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_collate='utf8mb4_0900_ai_ci',
        mysql_default_charset='utf8mb4',
        mysql_engine='InnoDB'
    )
    op.create_index('ix_password_reset_tokens_user_id', 'password_reset_tokens', ['user_id'], unique=False)
    op.create_index('ix_password_reset_tokens_token', 'password_reset_tokens', ['token'], unique=False)
    op.create_index('ix_password_reset_tokens_verification_code', 'password_reset_tokens', ['verification_code'], unique=False)
    op.create_index('ix_password_reset_tokens_id', 'password_reset_tokens', ['id'], unique=False)

    op.create_table(
        'token_blacklist',
        sa.Column('id', mysql.INTEGER(), autoincrement=True, nullable=False),
        sa.Column('jti', mysql.VARCHAR(length=255), nullable=False),
        sa.Column('user_id', mysql.INTEGER(), nullable=False),
        sa.Column('revoked', mysql.TINYINT(display_width=1), nullable=False),
        sa.Column('created_at', mysql.DATETIME(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('expires_at', mysql.DATETIME(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        mysql_collate='utf8mb4_0900_ai_ci',
        mysql_default_charset='utf8mb4',
        mysql_engine='InnoDB'
    )
    op.create_index('jti', 'token_blacklist', ['jti'], unique=False)
    op.create_index('ix_token_blacklist_id', 'token_blacklist', ['id'], unique=False)
