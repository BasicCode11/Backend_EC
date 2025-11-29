from enum import Enum
from typing import Optional , List
from datetime import datetime
from sqlalchemy import Column , Integer , String , ForeignKey , Float , DateTime
from sqlalchemy.orm import Mapped , mapped_column , relationship
from sqlalchemy.sql import func
from app.database import Base


class BrandStatus(str , Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"

class Brand(Base):
    __tablename__ = "brands"
    id : Mapped[int] = mapped_column(Integer , primary_key=True , index=True)
    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )
    logo : Mapped[str] = mapped_column(String(255) , nullable=False)
    logo_public_id : Mapped[str] = mapped_column(String(255) , nullable=False)
    name : Mapped[str] = mapped_column(String(100) , nullable=False)
    description : Mapped[str] = mapped_column(String(255) , nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), 
        nullable=False, 
        default=BrandStatus.ACTIVE.value,
        index=True
    )
    created_at : Mapped[datetime] = mapped_column(DateTime , nullable=False , server_default=func.now())
    updated_at : Mapped[datetime] = mapped_column(DateTime , nullable=False , server_default=func.now())
    
    products : Mapped[List["Product"]] = relationship(
        "Product",
        back_populates="brand",
        lazy="select"
    )
    user : Mapped["User"] = relationship(
        "User",
        back_populates="brands",
        lazy="select"
    )