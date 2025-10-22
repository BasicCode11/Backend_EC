from typing import Optional, Dict, Any, List
from sqlalchemy import String, Integer, DateTime, ForeignKey, DECIMAL, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database import Base


class ProductVariant(Base):
    __tablename__ = "product_variants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    sku: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    variant_name: Mapped[str] = mapped_column(String(255), nullable=False)
    attributes: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    price: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 2), nullable=True)
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
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

    @property
    def is_in_stock(self) -> bool:
        """Check if variant is in stock"""
        return self.stock_quantity > 0

    @property
    def attribute_summary(self) -> str:
        """Get a summary of variant attributes"""
        if not self.attributes:
            return ""
        return ", ".join([f"{k}: {v}" for k, v in self.attributes.items()])

    def __repr__(self) -> str:
        return f"<ProductVariant(id={self.id}, product_id={self.product_id}, name='{self.variant_name}')>"
