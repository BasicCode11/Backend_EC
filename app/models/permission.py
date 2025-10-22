from sqlalchemy import String, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base
from .role_has_permision import role_has_permission  # fixed import

class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    # Note: Based on your schema, permissions table doesn't have created_at/updated_at

    roles = relationship(
        "Role",
        secondary=role_has_permission,
        back_populates="permissions",
        lazy="selectin"
    )
