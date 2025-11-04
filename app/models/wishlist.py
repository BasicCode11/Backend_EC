from typing import Optional
from sqlalchemy import Integer, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database import Base


class Wishlist(Base):
    __tablename__ = "wishlists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), 
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
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="wishlist_items",
        lazy="select"
    )
    
    product: Mapped["Product"] = relationship(
        "Product",
        lazy="select"
    )
    
    variant: Mapped[Optional["ProductVariant"]] = relationship(
        "ProductVariant",
        lazy="select"
    )

    __table_args__ = (
        Index('idx_wishlist_user', 'user_id'),
        Index('idx_wishlist_product', 'product_id'),
        # Ensure user can't add same product+variant combination twice
        UniqueConstraint('user_id', 'product_id', 'variant_id', name='uq_user_product_variant'),
    )

    def __repr__(self) -> str:
        return f"<Wishlist(id={self.id}, user_id={self.user_id}, product_id={self.product_id})>"
