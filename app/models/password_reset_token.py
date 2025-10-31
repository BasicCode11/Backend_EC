from typing import Optional
from sqlalchemy import String, Integer, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime, timezone
from app.database import Base


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    verification_code: Mapped[str] = mapped_column(String(6), nullable=False, index=True)
    code_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    expires_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )

    # Relationship
    user: Mapped["User"] = relationship("User", lazy="select")

    @property
    def is_expired(self) -> bool:
        """Check if token has expired"""
        now = datetime.now(timezone.utc)
        # Handle timezone-naive datetime from database
        expires_at = self.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return now > expires_at

    @property
    def is_valid(self) -> bool:
        """Check if token is valid (not used and not expired)"""
        return not self.used and not self.is_expired
    
    @property
    def is_code_valid(self) -> bool:
        """Check if verification code can be used"""
        return not self.used and not self.is_expired and not self.code_verified

    def mark_as_used(self) -> None:
        """Mark token as used"""
        self.used = True
    
    def mark_code_verified(self) -> None:
        """Mark verification code as verified"""
        self.code_verified = True
