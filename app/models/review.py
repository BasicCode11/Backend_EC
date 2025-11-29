from typing import Optional
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Text, Index, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database import Base


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    order_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), 
        nullable=True, 
        index=True
    )
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    fit_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True) # 1=Small, 3=True, 5=Large
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    helpful_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
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
        back_populates="reviews",
        lazy="select"
    )
    
    user: Mapped["User"] = relationship(
        "User",
        back_populates="reviews",
        lazy="select"
    )
    
    order: Mapped[Optional["Order"]] = relationship(
        "Order",
        lazy="select"
    )

    __table_args__ = (
        Index('idx_review_product', 'product_id'),
        Index('idx_review_user', 'user_id'),
        Index('idx_review_order', 'order_id'),
        Index('idx_review_approved', 'is_approved'),
        Index('idx_review_rating', 'rating'),
        CheckConstraint('rating >= 1 AND rating <= 5', name='check_rating_range'),
        CheckConstraint('fit_rating >= 1 AND fit_rating <= 5', name='check_fit_rating_range'),
    )

    @property
    def is_verified_purchase(self) -> bool:
        """Check if this is a verified purchase review"""
        return self.order_id is not None

    @property
    def is_helpful(self) -> bool:
        """Check if review is considered helpful"""
        return self.helpful_count > 0

    def increment_helpful_count(self) -> None:
        """Increment helpful count"""
        self.helpful_count += 1

    def decrement_helpful_count(self) -> None:
        """Decrement helpful count (minimum 0)"""
        if self.helpful_count > 0:
            self.helpful_count -= 1

    def __repr__(self) -> str:
        return f"<Review(id={self.id}, product_id={self.product_id}, user_id={self.user_id}, rating={self.rating})>"
