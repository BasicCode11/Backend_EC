from enum import Enum
from sqlalchemy import CheckConstraint
from typing import Optional
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Text, DECIMAL
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database import Base

class AddressType(Enum):
    HOME = "home"
    WORK = "work"
    BILLING = "billing"
    SHIPPING = "shipping"
    OTHER = "other"

class UserAddress(Base):
    __tablename__ = "user_addresses"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False,
        index=True  # Added index for better performance
    )
    address_type: Mapped[str] = mapped_column(
        String(50), 
        nullable=False, 
        default=AddressType.HOME.value
    )
    label: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Custom label like "My Home"
    recipient_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)  # For gift addresses
    company: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    street_address: Mapped[str] = mapped_column(Text, nullable=False)
    apartment_suite: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Apt, Suite, etc.
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False, default="US")
    postal_code: Mapped[str] = mapped_column(String(20), nullable=False)
    longitude: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 7), nullable=True)  # Range: -180 to 180, precision: 7 decimals (~1.1cm accuracy)
    latitude: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 7), nullable=True)  # Range: -90 to 90, precision: 7 decimals (~1.1cm accuracy)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now()
    )
    
    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="addresses", lazy="select")
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "address_type IN ('home', 'work', 'billing', 'shipping', 'other')",
            name="check_address_type"
        ),
    )