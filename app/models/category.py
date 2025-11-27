from typing import Optional, List
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database import Base


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"), 
        nullable=True, 
        index=True
    )
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    image_public_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
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

    # Self-referential relationship for hierarchical categories
    parent: Mapped[Optional["Category"]] = relationship(
        "Category",
        remote_side=[id],
        back_populates="children",
        lazy="select"
    )
    children: Mapped[List["Category"]] = relationship(
        "Category",
        back_populates="parent",
        lazy="select"
    )

    # Products relationship
    products: Mapped[List["Product"]] = relationship(
        "Product",
        back_populates="category",
        lazy="select"
    )

    __table_args__ = (
        Index('idx_category_parent', 'parent_id'),
        Index('idx_category_active', 'is_active'),
        Index('idx_category_sort', 'sort_order'),
    )

    @property
    def is_root(self) -> bool:
        """Check if this is a root category (no parent)"""
        return self.parent_id is None

    @property
    def has_children(self) -> bool:
        """Check if this category has child categories"""
        return len(self.children) > 0

    def get_all_children(self) -> List["Category"]:
        """Get all descendant categories recursively"""
        all_children = []
        for child in self.children:
            all_children.append(child)
            all_children.extend(child.get_all_children())
        return all_children

    def get_path(self) -> List["Category"]:
        """Get the full path from root to this category"""
        path = []
        current = self
        while current:
            path.insert(0, current)
            current = current.parent
        return path

    def __repr__(self) -> str:
        return f"<Category(id={self.id}, name='{self.name}', parent_id={self.parent_id})>"
