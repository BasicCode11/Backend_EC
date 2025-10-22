from enum import Enum
from typing import Optional, List
from sqlalchemy import String, Integer, Boolean, DateTime, DECIMAL, Text, Index, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database import Base


class DiscountType(Enum):
    PERCENTAGE = "percentage"
    FIXED_AMOUNT = "fixed_amount"


class ApplyTo(Enum):
    ORDER = "order"
    PRODUCT = "product"
    CATEGORY = "category"


class Discount(Base):
    __tablename__ = "discounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    discount_type: Mapped[str] = mapped_column(
        String(20), 
        nullable=False,
        index=True
    )
    discount_value: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)
    minimum_order_amount: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 2), nullable=True)
    maximum_discount_amount: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 2), nullable=True)
    usage_limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    used_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    valid_from: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_until: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    apply_to: Mapped[str] = mapped_column(
        String(20), 
        nullable=False,
        index=True
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(), 
        nullable=False
    )

    # Relationships
    applications: Mapped[List["DiscountApplication"]] = relationship(
        "DiscountApplication",
        back_populates="discount",
        lazy="select"
    )

    __table_args__ = (
        Index('idx_discount_type', 'discount_type'),
        Index('idx_discount_active', 'is_active'),
        Index('idx_discount_apply_to', 'apply_to'),
        Index('idx_discount_valid_from', 'valid_from'),
        Index('idx_discount_valid_until', 'valid_until'),
        CheckConstraint('discount_value > 0', name='check_discount_value_positive'),
        CheckConstraint('used_count >= 0', name='check_used_count_non_negative'),
    )

    @property
    def is_valid(self) -> bool:
        """Check if discount is currently valid"""
        if not self.is_active:
            return False
        
        from datetime import datetime
        now = datetime.now()
        
        if self.valid_from and now < self.valid_from:
            return False
            
        if self.valid_until and now > self.valid_until:
            return False
            
        if self.usage_limit and self.used_count >= self.usage_limit:
            return False
            
        return True

    @property
    def remaining_usage(self) -> Optional[int]:
        """Get remaining usage count"""
        if self.usage_limit is None:
            return None
        return max(0, self.usage_limit - self.used_count)

    @property
    def is_percentage_discount(self) -> bool:
        """Check if this is a percentage discount"""
        return self.discount_type == DiscountType.PERCENTAGE.value

    @property
    def is_fixed_amount_discount(self) -> bool:
        """Check if this is a fixed amount discount"""
        return self.discount_type == DiscountType.FIXED_AMOUNT.value

    def calculate_discount_amount(self, order_amount: float) -> float:
        """Calculate discount amount for given order amount"""
        if not self.is_valid:
            return 0.0
            
        if self.minimum_order_amount and order_amount < self.minimum_order_amount:
            return 0.0
            
        if self.is_percentage_discount:
            discount_amount = order_amount * (self.discount_value / 100)
        else:
            discount_amount = self.discount_value
            
        if self.maximum_discount_amount:
            discount_amount = min(discount_amount, self.maximum_discount_amount)
            
        return min(discount_amount, order_amount)

    def can_apply_to_order(self, order_amount: float) -> bool:
        """Check if discount can be applied to order"""
        return self.is_valid and (
            not self.minimum_order_amount or order_amount >= self.minimum_order_amount
        )

    def increment_usage(self) -> None:
        """Increment usage count"""
        self.used_count += 1

    def __repr__(self) -> str:
        return f"<Discount(id={self.id}, name='{self.name}', type='{self.discount_type}')>"
