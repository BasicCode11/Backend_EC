from typing import Optional
from sqlalchemy import String, Integer, DateTime, ForeignKey, DECIMAL, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database import Base


class Inventory(Base):
    __tablename__ = "inventory"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    variant_id: Mapped[int] = mapped_column(
        ForeignKey("product_variants.id", ondelete="CASCADE"), 
        nullable=False, 
        index=False
    )
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reserved_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    low_stock_threshold: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    reorder_level: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    sku: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    batch_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    expiry_date: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
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
    variant: Mapped["ProductVariant"] = relationship(
        "ProductVariant",
        back_populates="inventory",
        lazy="select"
    )

    __table_args__ = (
        Index('idx_inventory_variant', 'variant_id'),
        Index('idx_inventory_sku', 'sku'),
        Index('idx_inventory_stock', 'stock_quantity'),
    )

    @property
    def available_quantity(self) -> int:
        """Get available quantity (stock - reserved)"""
        return self.stock_quantity - self.reserved_quantity

    @property
    def is_low_stock(self) -> bool:
        """Check if inventory is below low stock threshold"""
        return self.available_quantity <= self.low_stock_threshold

    @property
    def needs_reorder(self) -> bool:
        """Check if inventory needs reordering"""
        return self.available_quantity <= self.reorder_level

    @property
    def is_expired(self) -> bool:
        """Check if inventory has expired"""
        if not self.expiry_date:
            return False
        from datetime import datetime
        return datetime.now() > self.expiry_date

    def reserve_quantity(self, quantity: int) -> bool:
        """Reserve quantity if available"""
        if self.available_quantity >= quantity:
            self.reserved_quantity += quantity
            return True
        return False

    def release_quantity(self, quantity: int) -> bool:
        """Release reserved quantity"""
        if self.reserved_quantity >= quantity:
            self.reserved_quantity -= quantity
            return True
        return False

    def __repr__(self) -> str:
        return f"<Inventory(id={self.id}, variant_id={self.variant_id}, stock={self.stock_quantity}, reserved={self.reserved_quantity})>"
