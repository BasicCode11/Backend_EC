from typing import Optional
from sqlalchemy import String, Integer, DateTime, ForeignKey, DECIMAL, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database import Base


class CartItem(Base):
    __tablename__ = "cart_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    cart_id: Mapped[int] = mapped_column(
        ForeignKey("shopping_cart.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    variant_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("product_variants.id", ondelete="CASCADE"), 
        nullable=True, 
        index=True
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)
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
    cart: Mapped["ShoppingCart"] = relationship(
        "ShoppingCart",
        back_populates="items",
        lazy="select"
    )
    
    product: Mapped["Product"] = relationship(
        "Product",
        back_populates="cart_items",
        lazy="select"
    )
    
    variant: Mapped[Optional["ProductVariant"]] = relationship(
        "ProductVariant",
        back_populates="cart_items",
        lazy="select"
    )

    __table_args__ = (
        Index('idx_cart_item_cart', 'cart_id'),
        Index('idx_cart_item_product', 'product_id'),
        Index('idx_cart_item_variant', 'variant_id'),
    )

    @property
    def total_price(self) -> float:
        """Calculate total price for this cart item"""
        return float(self.price * self.quantity)

    @property
    def product_name(self) -> str:
        """Get product name with variant if applicable"""
        if self.variant:
            return f"{self.product.name} - {self.variant.variant_name}"
        return self.product.name

    @property
    def effective_price(self) -> float:
        """Get effective price (variant price or product price)"""
        if self.variant and self.variant.price:
            return float(self.variant.price)
        return float(self.product.price)

    def update_quantity(self, new_quantity: int) -> None:
        """Update quantity and recalculate price"""
        self.quantity = new_quantity
        self.price = self.effective_price

    def __repr__(self) -> str:
        return f"<CartItem(id={self.id}, cart_id={self.cart_id}, product_id={self.product_id}, quantity={self.quantity})>"
