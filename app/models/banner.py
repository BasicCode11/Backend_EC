from enum import Enum
from typing import Optional , List
from datetime import datetime
from sqlalchemy import Column , Integer , String , ForeignKey , Float , DateTime
from sqlalchemy.orm import Mapped , mapped_column , relationship
from sqlalchemy.sql import func
from app.database import Base

class BannerStatus(str , Enum):
    OPEN = "open"
    CLOSED = "closed"

class Banner(Base):
    __tablename__ = "banners"
    id : Mapped[int] = mapped_column(Integer , primary_key=True , index=True)
    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )
    image : Mapped[str] = mapped_column(String(255) , nullable=False)
    image_public_id : Mapped[str] = mapped_column(String(255) , nullable=False)
    title : Mapped[str] = mapped_column(String(100) , nullable=False)
    description : Mapped[Optional[str]] = mapped_column(String(255) , nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), 
        nullable=False, 
        default=BannerStatus.OPEN.value,
        index=True
    )
    slug : Mapped[Optional[str]] = mapped_column(String(100) , nullable=True , unique=True , index=True)
    start_date : Mapped[Optional[datetime]] = mapped_column(DateTime , nullable=True)
    end_date : Mapped[Optional[datetime]] = mapped_column(DateTime , nullable=True)
    created_at : Mapped[datetime] = mapped_column(DateTime , nullable=False , server_default=func.now())
    updated_at : Mapped[datetime] = mapped_column(DateTime , nullable=False , server_default=func.now())
    
    user : Mapped["User"] = relationship(
        "User",
        back_populates="banners",
        lazy="select"
    )