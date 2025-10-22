from sqlalchemy import Integer, DateTime, ForeignKey, DECIMAL, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database import Base


class DiscountApplication(Base):
    __tablename__ = "discount_applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    discount_id: Mapped[int] = mapped_column(
        ForeignKey("discounts.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    discount_amount: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )

    # Relationships
    discount: Mapped["Discount"] = relationship(
        "Discount",
        back_populates="applications",
        lazy="select"
    )
    
    order: Mapped["Order"] = relationship(
        "Order",
        back_populates="discount_applications",
        lazy="select"
    )
    
    user: Mapped["User"] = relationship(
        "User",
        lazy="select"
    )

    __table_args__ = (
        Index('idx_discount_app_discount', 'discount_id'),
        Index('idx_discount_app_order', 'order_id'),
        Index('idx_discount_app_user', 'user_id'),
    )

    def __repr__(self) -> str:
        return f"<DiscountApplication(id={self.id}, discount_id={self.discount_id}, order_id={self.order_id}, amount={self.discount_amount})>"
