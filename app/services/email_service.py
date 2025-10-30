from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.email_notification import EmailNotification, EmailStatus
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """
    Email service for sending emails.
    This is a basic implementation that logs emails.
    In production, integrate with SMTP, SendGrid, AWS SES, etc.
    """

    @staticmethod
    def send_email(
        db: Session,
        recipient_email: str,
        subject: str,
        template_name: str,
        content: str
    ) -> EmailNotification:
        """
        Send an email and log it to the database.
        
        Args:
            db: Database session
            recipient_email: Recipient's email address
            subject: Email subject
            template_name: Template identifier
            content: Email content/body
            
        Returns:
            EmailNotification: The created email notification record
        """
        email_notification = EmailNotification(
            recipient_email=recipient_email,
            subject=subject,
            template_name=template_name,
            content=content,
            status=EmailStatus.PENDING.value
        )
        db.add(email_notification)
        db.commit()
        db.refresh(email_notification)

        try:
            # TODO: Integrate with actual email service (SMTP, SendGrid, etc.)
            # For now, just log the email
            logger.info("="*80)
            logger.info(f"[EMAIL] To: {recipient_email}")
            logger.info(f"[EMAIL] Subject: {subject}")
            logger.info(f"[EMAIL] Template: {template_name}")
            logger.info(f"[EMAIL] Content:\n{content}")
            logger.info("="*80)
            
            # Mark as sent
            email_notification.status = EmailStatus.SENT.value
            email_notification.sent_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(email_notification)
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            email_notification.status = EmailStatus.FAILED.value
            email_notification.error_message = str(e)
            db.commit()
            db.refresh(email_notification)

        return email_notification

    @staticmethod
    def send_verification_email(
        db: Session,
        recipient_email: str,
        verification_token: str,
        frontend_url: str = "http://localhost:3000"
    ) -> EmailNotification:
        """Send email verification link"""
        verification_link = f"{frontend_url}/verify-email/{verification_token}"
        
        content = f"""
        Hello,
        
        Thank you for registering! Please verify your email address by clicking the link below:
        
        {verification_link}
        
        This link will expire in 24 hours.
        
        If you didn't create an account, please ignore this email.
        
        Best regards,
        Your E-commerce Team
        """
        
        return EmailService.send_email(
            db=db,
            recipient_email=recipient_email,
            subject="Verify Your Email Address",
            template_name="email_verification",
            content=content
        )

    @staticmethod
    def send_password_reset_email(
        db: Session,
        recipient_email: str,
        reset_token: str,
        frontend_url: str = "http://localhost:3000"
    ) -> EmailNotification:
        """Send password reset link"""
        reset_link = f"{frontend_url}/reset-password/{reset_token}"
        
        content = f"""
        Hello,
        
        We received a request to reset your password. Click the link below to reset it:
        
        {reset_link}
        
        This link will expire in 1 hour.
        
        If you didn't request a password reset, please ignore this email or contact support if you have concerns.
        
        Best regards,
        Your E-commerce Team
        """
        
        return EmailService.send_email(
            db=db,
            recipient_email=recipient_email,
            subject="Reset Your Password",
            template_name="password_reset",
            content=content
        )

    @staticmethod
    def send_password_changed_notification(
        db: Session,
        recipient_email: str
    ) -> EmailNotification:
        """Send notification that password was changed"""
        content = """
        Hello,
        
        This email confirms that your password has been successfully changed.
        
        If you didn't make this change, please contact our support team immediately.
        
        Best regards,
        Your E-commerce Team
        """
        
        return EmailService.send_email(
            db=db,
            recipient_email=recipient_email,
            subject="Password Changed Successfully",
            template_name="password_changed",
            content=content
        )
