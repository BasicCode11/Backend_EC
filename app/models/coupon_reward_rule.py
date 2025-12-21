"""
Coupon Reward Rule Model

This model defines the rules for automatically generating coupon codes for customers.
Two types of rules are supported:
1. ORDER_AMOUNT: Customer receives a coupon when their order total reaches a certain amount
2. ORDER_COUNT: Customer receives a coupon after placing a certain number of orders
"""

from enum import Enum
from typing import Optional, List
from sqlalchemy import String, Integer, Boolean, DateTime, DECIMAL, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database import Base


class RewardTriggerType(str, Enum):
    ORDER_AMOUNT = "order_amount"  # Trigger when order amount >= threshold
    ORDER_COUNT = "order_count"    # Trigger when order count >= threshold


class CouponRewardRule(Base):
    """
    Defines rules for automatic coupon generation.
    
    Examples:
    - Spend $100+ → Get 10% off coupon
    - Place 10 orders → Get $20 off coupon
    """
    __tablename__ = "coupon_reward_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Trigger configuration
    trigger_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    threshold_amount: Mapped[Optional[float]] = mapped_column(
        DECIMAL(10, 2), nullable=True,
        comment="Minimum order amount to trigger (for ORDER_AMOUNT type)"
    )
    threshold_count: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True,
        comment="Number of orders to trigger (for ORDER_COUNT type)"
    )
    
    # Coupon configuration (what the customer receives)
    coupon_discount_type: Mapped[str] = mapped_column(
        String(20), nullable=False,
        comment="'percentage' or 'fixed_amount'"
    )
    coupon_discount_value: Mapped[float] = mapped_column(
        DECIMAL(10, 2), nullable=False,
        comment="Discount value (percentage or fixed amount)"
    )
    coupon_minimum_order: Mapped[Optional[float]] = mapped_column(
        DECIMAL(10, 2), nullable=True,
        comment="Minimum order amount to use the coupon"
    )
    coupon_maximum_discount: Mapped[Optional[float]] = mapped_column(
        DECIMAL(10, 2), nullable=True,
        comment="Maximum discount amount (for percentage discounts)"
    )
    coupon_valid_days: Mapped[int] = mapped_column(
        Integer, default=30, nullable=False,
        comment="Number of days the coupon is valid after generation"
    )
    
    # Rule settings
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_one_time: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False,
        comment="If true, customer can only receive this coupon once"
    )
    priority: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False,
        comment="Higher priority rules are evaluated first"
    )
    
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationship to generated coupons
    user_coupons: Mapped[List["UserCoupon"]] = relationship(
        "UserCoupon",
        back_populates="reward_rule",
        lazy="select"
    )

    __table_args__ = (
        Index('idx_coupon_rule_trigger', 'trigger_type'),
        Index('idx_coupon_rule_active', 'is_active'),
    )

    def __repr__(self) -> str:
        return f"<CouponRewardRule(id={self.id}, name='{self.name}', trigger='{self.trigger_type}')>"
