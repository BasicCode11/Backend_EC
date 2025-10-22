from enum import Enum
from typing import Optional, Dict, Any
from sqlalchemy import String, Integer, DateTime, ForeignKey, DECIMAL, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database import Base


class PaymentMethod(Enum):
    CREDIT_CARD = "credit_card"
    PAYPAL = "paypal"
    BANK_TRANSFER = "bank_transfer"
    COD = "cod"


class PaymentStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    payment_method: Mapped[str] = mapped_column(
        String(20), 
        nullable=False,
        index=True
    )
    payment_gateway_transaction_id: Mapped[Optional[str]] = mapped_column(
        String(255), 
        nullable=True, 
        index=True
    )
    amount: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), 
        nullable=False, 
        default=PaymentStatus.PENDING.value,
        index=True
    )
    gateway_response: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
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
    order: Mapped["Order"] = relationship(
        "Order",
        back_populates="payments",
        lazy="select"
    )

    __table_args__ = (
        Index('idx_payment_order', 'order_id'),
        Index('idx_payment_method', 'payment_method'),
        Index('idx_payment_status', 'status'),
        Index('idx_payment_transaction', 'payment_gateway_transaction_id'),
    )

    @property
    def is_successful(self) -> bool:
        """Check if payment is successful"""
        return self.status == PaymentStatus.COMPLETED.value

    @property
    def is_failed(self) -> bool:
        """Check if payment failed"""
        return self.status == PaymentStatus.FAILED.value

    @property
    def is_pending(self) -> bool:
        """Check if payment is pending"""
        return self.status == PaymentStatus.PENDING.value

    @property
    def is_refunded(self) -> bool:
        """Check if payment is refunded"""
        return self.status == PaymentStatus.REFUNDED.value

    def can_be_refunded(self) -> bool:
        """Check if payment can be refunded"""
        return self.status == PaymentStatus.COMPLETED.value

    def __repr__(self) -> str:
        return f"<Payment(id={self.id}, order_id={self.order_id}, method='{self.payment_method}', status='{self.status}')>"
