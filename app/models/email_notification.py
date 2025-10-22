from enum import Enum
from typing import Optional
from sqlalchemy import String, Integer, DateTime, Text, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.database import Base


class EmailStatus(Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class EmailNotification(Base):
    __tablename__ = "email_notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    recipient_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    template_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), 
        nullable=False, 
        default=EmailStatus.PENDING.value,
        index=True
    )
    sent_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )

    __table_args__ = (
        Index('idx_email_recipient', 'recipient_email'),
        Index('idx_email_template', 'template_name'),
        Index('idx_email_status', 'status'),
        Index('idx_email_created', 'created_at'),
    )

    @property
    def is_pending(self) -> bool:
        """Check if email is pending"""
        return self.status == EmailStatus.PENDING.value

    @property
    def is_sent(self) -> bool:
        """Check if email was sent successfully"""
        return self.status == EmailStatus.SENT.value

    @property
    def is_failed(self) -> bool:
        """Check if email failed to send"""
        return self.status == EmailStatus.FAILED.value

    def mark_as_sent(self) -> None:
        """Mark email as sent"""
        self.status = EmailStatus.SENT.value
        self.sent_at = func.now()

    def mark_as_failed(self, error_message: str) -> None:
        """Mark email as failed with error message"""
        self.status = EmailStatus.FAILED.value
        self.error_message = error_message

    def __repr__(self) -> str:
        return f"<EmailNotification(id={self.id}, recipient='{self.recipient_email}', status='{self.status}')>"
