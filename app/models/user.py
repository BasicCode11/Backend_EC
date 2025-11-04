from typing import Optional, List
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Text 
from sqlalchemy.orm import Mapped, mapped_column, relationship 
from sqlalchemy.sql import func 
from app.database import Base 
from app.utils.validation import CommonValidation

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    picture: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_login_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    role: Mapped["Role"] = relationship(
        "Role",
        back_populates="users",
        lazy="select"
    )
    
    addresses: Mapped[List["UserAddress"]] = relationship(
        "UserAddress",
        back_populates="user",
        lazy="select",
        cascade="all, delete-orphan"
    )
    
    cart: Mapped[Optional["ShoppingCart"]] = relationship(
        "ShoppingCart",
        back_populates="user",
        lazy="select",
        uselist=False
    )
    
    orders: Mapped[List["Order"]] = relationship(
        "Order",
        back_populates="user",
        lazy="select"
    )
    
    reviews: Mapped[List["Review"]] = relationship(
        "Review",
        back_populates="user",
        lazy="select"
    )
    
    wishlist_items: Mapped[List["Wishlist"]] = relationship(
        "Wishlist",
        back_populates="user",
        lazy="select",
        cascade="all, delete-orphan"
    )
    
    discount_applications: Mapped[List["DiscountApplication"]] = relationship(
        "DiscountApplication",
        back_populates="user",
        lazy="select"
    )


    

    # Properties
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def permissions(self) -> list[str]:
        if not self.role:
            return []
        return self.role.get_permission_names()

    @property
    def is_active(self) -> bool:
        return self.email_verified

