from typing import Optional, List
from sqlalchemy import String, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database import Base


class ShoppingCart(Base):
    __tablename__ = "shopping_cart"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=True, 
        index=True
    )
    session_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
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
    user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="cart",
        lazy="select"
    )
    
    items: Mapped[List["CartItem"]] = relationship(
        "CartItem",
        back_populates="cart",
        lazy="select",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index('idx_cart_user', 'user_id'),
        Index('idx_cart_session', 'session_id'),
    )

    @property
    def total_items(self) -> int:
        """Get total number of items in cart"""
        return sum(item.quantity for item in self.items)

    @property
    def total_amount(self) -> float:
        """Get total amount of all items in cart"""
        return sum(item.total_price for item in self.items)

    @property
    def is_empty(self) -> bool:
        """Check if cart is empty"""
        return len(self.items) == 0

    def get_item_by_product(self, product_id: int, variant_id: Optional[int] = None) -> Optional["CartItem"]:
        """Get cart item by product and variant"""
        for item in self.items:
            if item.product_id == product_id and item.variant_id == variant_id:
                return item
        return None

    def add_item(self, product_id: int, quantity: int, price: float, variant_id: Optional[int] = None) -> "CartItem":
        """Add item to cart or update existing item"""
        existing_item = self.get_item_by_product(product_id, variant_id)
        if existing_item:
            existing_item.quantity += quantity
            existing_item.price = price  # Update price in case it changed
            return existing_item
        else:
            # This would typically be created through the CartItem model
            # For now, return None as the actual creation should be handled by the service layer
            return None

    def remove_item(self, product_id: int, variant_id: Optional[int] = None) -> bool:
        """Remove item from cart"""
        item = self.get_item_by_product(product_id, variant_id)
        if item:
            self.items.remove(item)
            return True
        return False

    def clear(self) -> None:
        """Clear all items from cart"""
        self.items.clear()

    def __repr__(self) -> str:
        return f"<ShoppingCart(id={self.id}, user_id={self.user_id}, items={len(self.items)})>"
