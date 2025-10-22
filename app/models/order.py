from enum import Enum
from typing import Optional, List
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, DECIMAL, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database import Base


class OrderStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class PaymentStatus(Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    status: Mapped[str] = mapped_column(
        String(20), 
        nullable=False, 
        default=OrderStatus.PENDING.value,
        index=True
    )
    subtotal: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)
    tax_amount: Mapped[float] = mapped_column(DECIMAL(10, 2), default=0.0, nullable=False)
    shipping_amount: Mapped[float] = mapped_column(DECIMAL(10, 2), default=0.0, nullable=False)
    discount_amount: Mapped[float] = mapped_column(DECIMAL(10, 2), default=0.0, nullable=False)
    total_amount: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)
    payment_status: Mapped[str] = mapped_column(
        String(20), 
        nullable=False, 
        default=PaymentStatus.PENDING.value,
        index=True
    )
    shipping_address_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("user_addresses.id", ondelete="SET NULL"), 
        nullable=True, 
        index=True
    )
    billing_address_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("user_addresses.id", ondelete="SET NULL"), 
        nullable=True, 
        index=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
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
    user: Mapped["User"] = relationship(
        "User",
        back_populates="orders",
        lazy="select"
    )
    
    items: Mapped[List["OrderItem"]] = relationship(
        "OrderItem",
        back_populates="order",
        lazy="select",
        cascade="all, delete-orphan"
    )
    
    payments: Mapped[List["Payment"]] = relationship(
        "Payment",
        back_populates="order",
        lazy="select",
        cascade="all, delete-orphan"
    )
    
    shipping_address: Mapped[Optional["UserAddress"]] = relationship(
        "UserAddress",
        foreign_keys=[shipping_address_id],
        lazy="select"
    )
    
    billing_address: Mapped[Optional["UserAddress"]] = relationship(
        "UserAddress",
        foreign_keys=[billing_address_id],
        lazy="select"
    )
    
    discount_applications: Mapped[List["DiscountApplication"]] = relationship(
        "DiscountApplication",
        back_populates="order",
        lazy="select"
    )

    __table_args__ = (
        Index('idx_order_user', 'user_id'),
        Index('idx_order_status', 'status'),
        Index('idx_order_payment_status', 'payment_status'),
        Index('idx_order_number', 'order_number'),
    )

    @property
    def is_paid(self) -> bool:
        """Check if order is paid"""
        return self.payment_status == PaymentStatus.PAID.value

    @property
    def is_cancelled(self) -> bool:
        """Check if order is cancelled"""
        return self.status == OrderStatus.CANCELLED.value

    @property
    def is_delivered(self) -> bool:
        """Check if order is delivered"""
        return self.status == OrderStatus.DELIVERED.value

    @property
    def total_items(self) -> int:
        """Get total number of items in order"""
        return sum(item.quantity for item in self.items)

    @property
    def can_be_cancelled(self) -> bool:
        """Check if order can be cancelled"""
        return self.status in [OrderStatus.PENDING.value, OrderStatus.PROCESSING.value]

    def calculate_totals(self) -> None:
        """Recalculate order totals"""
        self.subtotal = sum(item.total_price for item in self.items)
        self.total_amount = self.subtotal + self.tax_amount + self.shipping_amount - self.discount_amount

    def __repr__(self) -> str:
        return f"<Order(id={self.id}, order_number='{self.order_number}', status='{self.status}')>"
