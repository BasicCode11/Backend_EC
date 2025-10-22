from sqlalchemy import String, Integer, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship 
from sqlalchemy.sql import func
from app.database import Base
from .role_has_permision import role_has_permission
from typing import List, Set


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    users: Mapped[List["User"]] = relationship(
        "User",
        back_populates="role",
        lazy="select"
    )

    permissions: Mapped[List["Permission"]] = relationship(
        "Permission",
        secondary=role_has_permission,
        back_populates="roles",
        lazy="selectin"
    )

    __table_args__ = (
        Index('idx_role_name', 'name'),
    )

    def get_all_permissions(self) -> Set["Permission"]:
        return set(self.permissions)

    def get_permission_names(self) -> List[str]:
        return [perm.name for perm in self.permissions]

    def has_permission(self, permission_name: str) -> bool:
        return permission_name in self.get_permission_names()

    def __repr__(self) -> str:
        return f"<Role(id={self.id}, name='{self.name}')>"
