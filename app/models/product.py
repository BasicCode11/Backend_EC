from enum import Enum
from typing import Optional, List, Dict, Any
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Text, DECIMAL, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database import Base


class ProductStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"


class Product(Base):
    __tablename__ = "products"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    material: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    care_instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)
    compare_price: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 2), nullable=True)
    cost_price: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 2), nullable=True)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    brand_id : Mapped[int] = mapped_column(
        ForeignKey("brands.id", ondelete="SET NULL"), 
        nullable=True, 
        index=True
    )
    weight: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 2), nullable=True)
    dimensions: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), 
        nullable=False, 
        default=ProductStatus.ACTIVE.value,
        index=True
    )
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
    brand : Mapped["Brand"] = relationship(
        "Brand",
        back_populates="products",
        lazy="select"
    )
    # Relationships
    category: Mapped["Category"] = relationship(
        "Category",
        back_populates="products",
        lazy="select"
    )
    
    images: Mapped[List["ProductImage"]] = relationship(
        "ProductImage",
        back_populates="product",
        lazy="select",
        cascade="all, delete-orphan"
    )
    
    variants: Mapped[List["ProductVariant"]] = relationship(
        "ProductVariant",
        back_populates="product",
        lazy="select",
        cascade="all, delete-orphan"
    )
    
    cart_items: Mapped[List["CartItem"]] = relationship(
        "CartItem",
        back_populates="product",
        lazy="select"
    )
    
    order_items: Mapped[List["OrderItem"]] = relationship(
        "OrderItem",
        back_populates="product",
        lazy="select"
    )
    
    reviews: Mapped[List["Review"]] = relationship(
        "Review",
        back_populates="product",
        lazy="select"
    )

    __table_args__ = (
        Index('idx_product_category', 'category_id'),
        Index('idx_product_status', 'status'),
        Index('idx_product_featured', 'featured'),
        Index('idx_product_price', 'price'),
    )

    @property
    def is_active(self) -> bool:
        """Check if product is active"""
        return self.status == ProductStatus.ACTIVE.value

    @property
    def primary_image(self) -> Optional["ProductImage"]:
        """Get the primary product image"""
        for image in self.images:
            if image.is_primary:
                return image
        return self.images[0] if self.images else None

    @property
    def total_stock(self) -> int:
        """Get total stock quantity across all inventory records"""
        return sum(inv.stock_quantity for inv in self.inventory)

    @property
    def average_rating(self) -> Optional[float]:
        """Calculate average rating from reviews"""
        if not self.reviews:
            return None
        approved_reviews = [r for r in self.reviews if r.is_approved]
        if not approved_reviews:
            return None
        return sum(r.rating for r in approved_reviews) / len(approved_reviews)

    @property
    def review_count(self) -> int:
        """Get count of approved reviews"""
        return len([r for r in self.reviews if r.is_approved])

    def __repr__(self) -> str:
        return f"<Product(id={self.id}, name='{self.name}', status='{self.status}')>"
