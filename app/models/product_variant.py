from typing import Optional, Dict, Any, List, TYPE_CHECKING
if TYPE_CHECKING:
    from .product_image import ProductImage

from sqlalchemy import String, Integer, DateTime, ForeignKey, DECIMAL, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database import Base


class ProductVariant(Base):
    """
    Product Variant Model - Represents different variations of a product.
    
    NOTE: Stock is NOT tracked here. Use the Inventory table to manage stock.
    Variants define product options (size, color, etc.) and optional pricing.
    """
    __tablename__ = "product_variants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), 
        nullable=False, 
        index=True
    )
    sku: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True, unique=True)
    variant_name: Mapped[str] = mapped_column(String(255), nullable=True)
    color: Mapped[str] = mapped_column(String(50) , nullable=True)
    size: Mapped[str] = mapped_column(String(50) , nullable=True)
    weight: Mapped[str] = mapped_column(String(20) , nullable=True)
    additional_price: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 2), nullable=True) # Database column (to be migrated)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
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
    product: Mapped["Product"] = relationship(
        "Product",
        back_populates="variants",
        lazy="select"
    )
    inventory: Mapped[List["Inventory"]] = relationship(
        "Inventory",
        back_populates="variant",
        lazy="select"
    )
    
    cart_items: Mapped[List["CartItem"]] = relationship(
        "CartItem",
        back_populates="variant",
        lazy="select"
    )
    
    order_items: Mapped[List["OrderItem"]] = relationship(
        "OrderItem",
        back_populates="variant",
        lazy="select"
    )

    __table_args__ = (
        Index('idx_variant_product', 'product_id'),
        Index('idx_variant_sku', 'sku'),
        Index('idx_variant_sort', 'sort_order'),
    )

    @property
    def effective_price(self) -> float:
        """Get effective price (variant price or product price)"""
        return self.price if self.price is not None else self.product.price

    # NOTE: stock_quantity is now a database column, not a computed property
    # This will be migrated to the Inventory table in a future update
    # @property
    # def stock_quantity(self) -> int:
    #     """
    #     Get total stock quantity from Inventory table.
    #     
    #     IMPORTANT: This queries the Inventory table for the parent product.
    #     Stock is managed via Inventory, not stored on the variant itself.
    #     """
    #     if not self.product or not self.product.inventory:
    #         return 0
    #     return sum(inv.available_quantity for inv in self.product.inventory)

    @property
    def is_in_stock(self) -> bool:
        """Check if variant has available stock"""
        return self.stock_quantity > 0

    def get_available_stock(self) -> int:
        """
        Get available stock quantity from all inventory locations.
        Returns the sum of available quantities (stock - reserved) across all inventory records.
        """
        if not self.product or not self.product.inventory:
            return 0
        return sum(inv.available_quantity for inv in self.product.inventory)

    def __repr__(self) -> str:
        return f"<ProductVariant(id={self.id}, product_id={self.product_id}, name='{self.variant_name}')>"
