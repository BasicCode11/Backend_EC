"""add_coupon_reward_tables_and_fields

Revision ID: 1c0ab6876c2c
Revises: e69412ba6a27
Create Date: 2025-12-21 17:11:31.626213

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '1c0ab6876c2c'
down_revision = 'e69412ba6a27'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create coupon_reward_rules table
    op.create_table('coupon_reward_rules',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('trigger_type', sa.String(length=20), nullable=False),
        sa.Column('threshold_amount', sa.DECIMAL(precision=10, scale=2), nullable=True),
        sa.Column('threshold_count', sa.Integer(), nullable=True),
        sa.Column('coupon_discount_type', sa.String(length=20), nullable=False),
        sa.Column('coupon_discount_value', sa.DECIMAL(precision=10, scale=2), nullable=False),
        sa.Column('coupon_minimum_order', sa.DECIMAL(precision=10, scale=2), nullable=True),
        sa.Column('coupon_maximum_discount', sa.DECIMAL(precision=10, scale=2), nullable=True),
        sa.Column('coupon_valid_days', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('is_one_time', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_coupon_rule_active', 'coupon_reward_rules', ['is_active'], unique=False)
    op.create_index('idx_coupon_rule_trigger', 'coupon_reward_rules', ['trigger_type'], unique=False)
    op.create_index(op.f('ix_coupon_reward_rules_name'), 'coupon_reward_rules', ['name'], unique=False)

    # Create user_coupons table
    op.create_table('user_coupons',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('reward_rule_id', sa.Integer(), nullable=True),
        sa.Column('triggered_by_order_id', sa.Integer(), nullable=True),
        sa.Column('discount_type', sa.String(length=20), nullable=False),
        sa.Column('discount_value', sa.DECIMAL(precision=10, scale=2), nullable=False),
        sa.Column('minimum_order_amount', sa.DECIMAL(precision=10, scale=2), nullable=True),
        sa.Column('maximum_discount_amount', sa.DECIMAL(precision=10, scale=2), nullable=True),
        sa.Column('valid_from', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_used', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('used_on_order_id', sa.Integer(), nullable=True),
        sa.Column('email_sent', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('email_sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('name', sa.String(length=100), nullable=True),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('usage_limit', sa.Integer(), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['reward_rule_id'], ['coupon_reward_rules.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['triggered_by_order_id'], ['orders.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['used_on_order_id'], ['orders.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    op.create_index('idx_user_coupon_used', 'user_coupons', ['is_used'], unique=False)
    op.create_index('idx_user_coupon_user', 'user_coupons', ['user_id'], unique=False)
    op.create_index('idx_user_coupon_valid', 'user_coupons', ['valid_until'], unique=False)


def downgrade() -> None:
    op.drop_table('user_coupons')
    op.drop_table('coupon_reward_rules')
