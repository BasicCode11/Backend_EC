from typing import Optional, Dict, Any
from sqlalchemy import String, Integer, DateTime, ForeignKey, DECIMAL, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database import Base


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), 
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
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    product_sku: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    variant_attributes: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)
    total_price: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )

    # Relationships
    order: Mapped["Order"] = relationship(
        "Order",
        back_populates="items",
        lazy="select"
    )
    
    product: Mapped["Product"] = relationship(
        "Product",
        back_populates="order_items",
        lazy="select"
    )
    
    variant: Mapped[Optional["ProductVariant"]] = relationship(
        "ProductVariant",
        back_populates="order_items",
        lazy="select"
    )

    __table_args__ = (
        Index('idx_order_item_order', 'order_id'),
        Index('idx_order_item_product', 'product_id'),
        Index('idx_order_item_variant', 'variant_id'),
    )

    @property
    def display_name(self) -> str:
        """Get display name for the order item"""
        if self.variant and self.variant_attributes:
            attributes_str = ", ".join([f"{k}: {v}" for k, v in self.variant_attributes.items()])
            return f"{self.product_name} ({attributes_str})"
        return self.product_name

    @property
    def effective_sku(self) -> str:
        """Get effective SKU (variant SKU or product SKU)"""
        if self.variant and self.variant.sku:
            return self.variant.sku
        return self.product_sku or ""

    def calculate_total(self) -> None:
        """Calculate total price for this order item"""
        self.total_price = float(self.unit_price * self.quantity)

    def __repr__(self) -> str:
        return f"<OrderItem(id={self.id}, order_id={self.order_id}, product_name='{self.product_name}', quantity={self.quantity})>"
