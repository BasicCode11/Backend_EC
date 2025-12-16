from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from math import ceil

from app.database import get_db
from app.models.user import User
from app.models.email_notification import EmailNotification, EmailStatus
from app.deps.auth import require_permission , get_current_active_user
from pydantic import BaseModel
from app.services.email_service import EmailService
router = APIRouter()


# Response schemas
class EmailNotificationResponse(BaseModel):
    id: int
    recipient_email: str
    subject: str
    template_name: str
    content: Optional[str]
    status: str
    sent_at: Optional[datetime]
    error_message: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class EmailListResponse(BaseModel):
    items: List[EmailNotificationResponse]
    total: int
    page: int
    limit: int
    pages: int


class EmailStatsResponse(BaseModel):
    total_emails: int
    pending_count: int
    sent_count: int
    failed_count: int
    success_rate: float
    emails_today: int
    emails_this_week: int
    emails_this_month: int


@router.get("/admin/emails", response_model=EmailListResponse)
def get_email_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    template: Optional[str] = None,
    recipient: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    **Get email notification logs (Admin only)**
    
    View history of all emails sent by the system.
    
    **Filters:**
    - status: pending, sent, failed
    - template: Filter by email template name
    - recipient: Filter by recipient email
    
    **Use Cases:**
    - Monitor email delivery
    - Debug failed emails
    - Track email activity
    - Audit email communications
    
    Requires `admin:emails` permission.
    """
    query = db.query(EmailNotification)
    
    # Apply filters
    if status:
        query = query.filter(EmailNotification.status == status)
    
    if template:
        query = query.filter(EmailNotification.template_name == template)
    
    if recipient:
        query = query.filter(EmailNotification.recipient_email.contains(recipient))
    
    # Get total
    total = query.count()
    
    # Paginate
    skip = (page - 1) * limit
    emails = query.order_by(
        EmailNotification.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    pages = ceil(total / limit) if total > 0 else 1
    
    items = [EmailNotificationResponse.model_validate(email) for email in emails]
    
    return EmailListResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        pages=pages
    )


@router.get("/admin/emails/{email_id}", response_model=EmailNotificationResponse)
def get_email_details(
    email_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["admin:emails"]))
):
    """
    **Get email notification details (Admin only)**
    
    View full details of a specific email including content.
    """
    email = db.query(EmailNotification).filter(
        EmailNotification.id == email_id
    ).first()
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Email notification with ID {email_id} not found"
        )
    
    return EmailNotificationResponse.model_validate(email)


@router.get("/admin/emails/stats/summary", response_model=EmailStatsResponse)
def get_email_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["email:read"]))
):
    """
    **Get email statistics (Admin only)**
    
    Returns comprehensive email delivery statistics:
    - Total emails sent
    - Status breakdown (pending, sent, failed)
    - Success rate
    - Emails sent today, this week, this month
    
    Useful for monitoring email system health.
    """
    # Total counts by status
    total_emails = db.query(EmailNotification).count()
    pending_count = db.query(EmailNotification).filter(
        EmailNotification.status == EmailStatus.PENDING.value
    ).count()
    sent_count = db.query(EmailNotification).filter(
        EmailNotification.status == EmailStatus.SENT.value
    ).count()
    failed_count = db.query(EmailNotification).filter(
        EmailNotification.status == EmailStatus.FAILED.value
    ).count()
    
    # Calculate success rate
    if total_emails > 0:
        success_rate = (sent_count / total_emails) * 100
    else:
        success_rate = 0.0
    
    # Time-based counts
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = now - timedelta(days=7)
    month_start = now - timedelta(days=30)
    
    emails_today = db.query(EmailNotification).filter(
        EmailNotification.created_at >= today_start
    ).count()
    
    emails_this_week = db.query(EmailNotification).filter(
        EmailNotification.created_at >= week_start
    ).count()
    
    emails_this_month = db.query(EmailNotification).filter(
        EmailNotification.created_at >= month_start
    ).count()
    
    return EmailStatsResponse(
        total_emails=total_emails,
        pending_count=pending_count,
        sent_count=sent_count,
        failed_count=failed_count,
        success_rate=round(success_rate, 2),
        emails_today=emails_today,
        emails_this_week=emails_this_week,
        emails_this_month=emails_this_month
    )


@router.post("/admin/emails/{email_id}/resend")
def resend_failed_email(
    email_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["admin:emails"]))
):
    """
    **Resend a failed email (Admin only)**
    
    Retry sending an email that previously failed.
    
    **Use Cases:**
    - Retry after SMTP server issues
    - Resend after fixing email configuration
    - Manual retry for important emails
    
    **Note:** This creates a new email notification record.
    """
    # Get original email
    email = db.query(EmailNotification).filter(
        EmailNotification.id == email_id
    ).first()
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Email notification with ID {email_id} not found"
        )
    
    if email.status != EmailStatus.FAILED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only resend failed emails"
        )
    
    # Create new email notification (resend attempt)
    new_email = EmailNotification(
        recipient_email=email.recipient_email,
        subject=email.subject,
        template_name=email.template_name,
        content=email.content,
        status=EmailStatus.PENDING.value
    )
    
    db.add(new_email)
    db.commit()
    db.refresh(new_email)
    
    # TODO: Trigger email sending service here
    # For now, just mark as pending and let the email worker pick it up
    
    return {
        "message": "Email queued for resending",
        "original_id": email_id,
        "new_id": new_email.id,
        "recipient": email.recipient_email
    }


@router.get("/admin/emails/templates/list")
def get_email_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["email:read"]))
):
    """
    **Get list of email templates used (Admin only)**
    
    Returns all email template names that have been used,
    with count of emails sent for each template.
    
    Useful for understanding which emails are being sent most.
    """
    # Get unique templates with counts
    templates = db.query(
        EmailNotification.template_name,
        func.count(EmailNotification.id).label('count')
    ).group_by(
        EmailNotification.template_name
    ).all()
    
    result = [
        {
            "template_name": template[0],
            "email_count": template[1]
        }
        for template in templates
    ]
    
    return {
        "templates": result,
        "total_templates": len(result)
    }


@router.delete("/admin/emails/{email_id}")
def delete_email_log(
    email_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["admin:emails"]))
):
    """
    **Delete email log (Admin only)**
    
    Remove an email notification record from the database.
    Use with caution - this permanently deletes the log.
    """
    email = db.query(EmailNotification).filter(
        EmailNotification.id == email_id
    ).first()
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Email notification with ID {email_id} not found"
        )
    
    db.delete(email)
    db.commit()
    
    return {
        "message": "Email log deleted successfully",
        "email_id": email_id
    }


@router.post("/admin/emails/cleanup/old")
def cleanup_old_emails(
    days: int = Query(90, ge=1, description="Delete emails older than this many days"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["email:create"]))
):
    """
    **Cleanup old email logs (Admin only)**
    
    Delete email notification records older than specified days.
    Helps keep database clean and performant.
    
    **Default:** Deletes emails older than 90 days
    
    **Note:** Only deletes sent/failed emails, preserves pending.
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Only delete sent or failed emails (keep pending)
    deleted_count = db.query(EmailNotification).filter(
        EmailNotification.created_at < cutoff_date,
        EmailNotification.status.in_([EmailStatus.SENT.value, EmailStatus.FAILED.value])
    ).delete()
    
    db.commit()
    
    return {
        "message": f"Cleaned up old email logs",
        "days": days,
        "deleted_count": deleted_count,
        "cutoff_date": cutoff_date.isoformat()
    }


@router.post("customer/contactup")
def contachus(
    full_name: str,
    email_address: str,
    message: str,
    subject: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return EmailService.send_email_contactus(
        db=db,
        currenct_user=current_user,
        full_name=full_name,
        email_address=email_address,
        message=message,
        subject=subject
    )