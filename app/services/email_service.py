from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.email_notification import EmailNotification, EmailStatus
from app.core.config import settings  # ✅ Import your settings here
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class EmailService:
    """
    Email service for sending emails (via SMTP).
    Works with Gmail App Passwords or any SMTP service.
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

        # Create DB record first
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
            # ✅ Load SMTP Config from settings.py
            smtp_host = settings.SMTP_HOST
            smtp_port = settings.SMTP_PORT
            smtp_user = settings.SMTP_USER
            smtp_password = settings.SMTP_PASSWORD
            smtp_from_email = settings.SMTP_FROM_EMAIL or smtp_user
            smtp_from_name = settings.SMTP_FROM_NAME

            # ✅ Debug logs
            logger.info("=" * 80)
            logger.info(f"[EMAIL] Sending to: {recipient_email}")
            logger.info(f"[EMAIL] Subject: {subject}")
            logger.info(f"[EMAIL] Template: {template_name}")
            logger.info(f"[EMAIL] From: {smtp_from_name} <{smtp_from_email}>")
            logger.info(f"[EMAIL] SMTP: {smtp_host}:{smtp_port}")
            logger.info(f"[EMAIL] Content:\n{content}")
            logger.info("=" * 80)

            # ✅ Ensure SMTP credentials exist
            if not (smtp_host and smtp_user and smtp_password):
                logger.warning("⚠️ SMTP not configured. Email logged but not sent.")
                email_notification.status = EmailStatus.FAILED.value
                db.commit()
                return email_notification

            # ✅ Build email
            message = MIMEMultipart()
            message["From"] = f"{smtp_from_name} <{smtp_from_email}>"
            message["To"] = recipient_email
            message["Subject"] = subject
            message.attach(MIMEText(content, "plain"))

            # ✅ Send the email
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()  # Use TLS
                server.login(smtp_user, smtp_password)
                server.send_message(message)

            logger.info(f"✅ Email sent successfully to {recipient_email}")

            # ✅ Update DB
            email_notification.status = EmailStatus.SENT.value
            email_notification.sent_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(email_notification)

        except Exception as e:
            # ❌ Error handling
            logger.error(f"❌ Failed to send email: {str(e)}")
            email_notification.status = EmailStatus.FAILED.value
            email_notification.error_message = str(e)
            db.commit()
            db.refresh(email_notification)

        return email_notification

    # -------------------------
    # 📩 EMAIL TEMPLATES
    # -------------------------

    @staticmethod
    def send_verification_email(
        db: Session,
        recipient_email: str,
        frontend_url: str = "http://localhost:5173"
    ) -> EmailNotification:
        """Send email verification link"""
        verification_link = f"{frontend_url}"

        content = f"""
        Hello! I'm from Vortex store 😍,

        Thank you for registering! ! You can login to my store and buy whatever you want!

        {verification_link}

        This link will open web store .

        Thank you and happy shopping! 🛍️
        """

        try: 
            email_notification = EmailService.send_email(
                db=db,
                recipient_email=recipient_email,
                subject="Verify Your Email Address",
                template_name="email_verification",
                content=content
            )
            return email_notification
        except Exception as e:
            # If sending fails (SMTP down, invalid email, etc.)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to send verification email: {str(e)}"
            )

    @staticmethod
    def send_password_reset_email(
        db: Session,
        recipient_email: str,
        verification_code: str,
    ) -> EmailNotification:
        """Send password reset verification code"""

        content = f"""
        Hello,

        We received a request to reset your password. Use the verification code below:

        Verification Code: {verification_code}

        This code will expire in 15 minutes.

        If you didn't request a password reset, please ignore this email.

        Best regards,
        Your E-commerce Team
        """

        return EmailService.send_email(
            db=db,
            recipient_email=recipient_email,
            subject="Password Reset Verification Code",
            template_name="password_reset_code",
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

    @staticmethod
    def send_order_confirmation_email(
        db: Session,
        order
    ) -> EmailNotification:
        """Send order confirmation email"""
        
        items_list = "\n".join(
            f"- {item.product_name} (x{item.quantity}): ${item.total_price:.2f}"
            for item in order.items
        )
        
        content = f"""
        Dear {order.user.first_name},

        Thank you for your order! Your payment has been successful.
        Order Status:{order.status}
        Payment Status: {order.payment_status}
        Order Number: {order.order_number}
        Total Amount: ${order.total_amount:.2f}

        Items:
        {items_list}

        We've received your order and will process it shortly.

        Thank you for shopping with us!

        Best regards,
        Your E-commerce Team
        """
        
        return EmailService.send_email(
            db=db,
            recipient_email=order.user.email,
            subject=f"Order Confirmation #{order.order_number}",
            template_name="order_confirmation",
            content=content
        )
