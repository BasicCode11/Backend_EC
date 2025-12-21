
import secrets
from typing import Optional
from sqlalchemy import String, Integer, Boolean, DateTime, DECIMAL, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database import Base


class UserCoupon(Base):
    """
    A coupon generated for a specific user from a reward rule.
    """
    __tablename__ = "user_coupons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True, index=True
    )
    
    # Link to the rule that generated this coupon
    reward_rule_id: Mapped[int] = mapped_column(
        ForeignKey("coupon_reward_rules.id", ondelete="SET NULL"),
        nullable=True, index=True
    )
    
    # Link to the order that triggered this coupon (optional)
    triggered_by_order_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("orders.id", ondelete="SET NULL"),
        nullable=True, index=True
    )
    
    # Coupon details (copied from rule at time of creation)
    discount_type: Mapped[str] = mapped_column(String(20), nullable=False)
    discount_value: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)
    minimum_order_amount: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 2), nullable=True)
    maximum_discount_amount: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 2), nullable=True)
    
    # Validity
    valid_from: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    valid_until: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Usage tracking
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    used_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    used_on_order_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("orders.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Email notification tracking
    email_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email_sent_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Public coupon support (for admin-created coupons that anyone can use)
    is_public: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False,
        comment="If true, this coupon can be used by any user (promo code)"
    )
    name: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
        comment="Display name for the coupon (e.g., 'Summer Sale')"
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True,
        comment="Description of the coupon"
    )
    usage_limit: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True,
        comment="For public coupons: max number of times it can be used"
    )
    usage_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False,
        comment="For public coupons: how many times it has been used"
    )
    
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="user_coupons",
        lazy="select"
    )
    
    reward_rule: Mapped[Optional["CouponRewardRule"]] = relationship(
        "CouponRewardRule",
        back_populates="user_coupons",
        lazy="select"
    )
    
    triggered_by_order: Mapped[Optional["Order"]] = relationship(
        "Order",
        foreign_keys=[triggered_by_order_id],
        lazy="select"
    )

    __table_args__ = (
        Index('idx_user_coupon_user', 'user_id'),
        Index('idx_user_coupon_code', 'code'),
        Index('idx_user_coupon_used', 'is_used'),
        Index('idx_user_coupon_valid', 'valid_until'),
    )

    @staticmethod
    def generate_coupon_code(prefix="PROMO", length=5) -> str:
        """Generate a unique coupon code like REWARD-A1B2C3D4"""
        random_part = secrets.token_hex(length).upper()
        return f"{prefix}-{random_part}"
    
    @staticmethod
    def _make_aware(dt):
        """Ensure datetime is timezone-aware (UTC)"""
        from datetime import timezone
        if dt is None:
            return None
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt
    
    @property
    def is_valid(self) -> bool:
        """Check if coupon is currently valid and unused"""
        # For personal coupons, check if already used
        if not self.is_public and self.is_used:
            return False
        
        # For public coupons, check usage limit
        if self.is_public and self.usage_limit:
            if self.usage_count >= self.usage_limit:
                return False
        
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        
        valid_from = self._make_aware(self.valid_from)
        valid_until = self._make_aware(self.valid_until)
        
        if valid_from and now < valid_from:
            return False
        if valid_until and now > valid_until:
            return False
            
        return True
    
    @property
    def is_expired(self) -> bool:
        """Check if coupon has expired"""
        from datetime import datetime, timezone
        valid_until = self._make_aware(self.valid_until)
        if valid_until is None:
            return False
        return datetime.now(timezone.utc) > valid_until

    def calculate_discount_amount(self, order_amount: float) -> float:
        """Calculate discount amount for given order amount"""
        if not self.is_valid:
            return 0.0
            
        if self.minimum_order_amount and order_amount < float(self.minimum_order_amount):
            return 0.0
            
        if self.discount_type == "percentage":
            discount_amount = order_amount * (float(self.discount_value) / 100)
        else:
            discount_amount = float(self.discount_value)
            
        if self.maximum_discount_amount:
            discount_amount = min(discount_amount, float(self.maximum_discount_amount))
            
        return min(discount_amount, order_amount)

    def can_apply_to_order(self, order_amount: float) -> bool:
        """Check if coupon can be applied to order"""
        return self.is_valid and (
            not self.minimum_order_amount or order_amount >= float(self.minimum_order_amount)
        )

    def __repr__(self) -> str:
        return f"<UserCoupon(id={self.id}, code='{self.code}', user_id={self.user_id}, is_used={self.is_used})>"
