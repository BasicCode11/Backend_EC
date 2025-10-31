from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.audit_log import (
    AuditLogResponse,
    AuditLogFilter,
    AuditLogWithPagination,
    AuditLogWithUser
)
from app.services.audit_log_service import AuditLogService
from app.deps.auth import get_current_active_user, require_permission
from datetime import datetime

router = APIRouter()


@router.get("/audit-logs", response_model=AuditLogWithPagination)
def get_audit_logs(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=200, description="Items per page"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    action: Optional[str] = Query(None, description="Filter by action type"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    entity_id: Optional[int] = Query(None, description="Filter by entity ID"),
    entity_uuid: Optional[str] = Query(None, description="Filter by entity UUID"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["audit_logs:read"]))
):
    """Get audit logs with filters - requires audit_logs:read permission"""
    filters = AuditLogFilter(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        entity_uuid=entity_uuid,
        start_date=start_date,
        end_date=end_date,
        page=page,
        limit=limit
    )
    return AuditLogService.get_all(db, filters)


@router.get("/audit-logs/{log_id}", response_model=AuditLogWithUser)
def get_audit_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["audit_logs:read"]))
):
    """Get specific audit log by ID - requires audit_logs:read permission"""
    log = AuditLogService.get_by_id(db, log_id)
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit log not found"
        )
    
    return AuditLogWithUser(
        id=log.id,
        user_id=log.user_id,
        action=log.action,
        entity_type=log.entity_type,
        entity_id=log.entity_id,
        entity_uuid=log.entity_uuid,
        changes=log.changes,
        old_values=log.old_values,
        new_values=log.new_values,
        ip_address=log.ip_address,
        user_agent=log.user_agent,
        description=log.description,
        created_at=log.created_at,
        user_email=log.user.email if log.user else None,
        user_name=log.user.full_name if log.user else None
    )


@router.get("/audit-logs/user/{user_id}", response_model=AuditLogWithPagination)
def get_user_activity(
    user_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=200, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["audit_logs:read"]))
):
    """Get all activity logs for a specific user - requires audit_logs:read permission"""
    return AuditLogService.get_user_activity(db, user_id, page, limit)


@router.get("/audit-logs/entity/{entity_type}/{entity_id}", response_model=AuditLogWithPagination)
def get_entity_history(
    entity_type: str,
    entity_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=200, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["audit_logs:read"]))
):
    """Get audit history for a specific entity - requires audit_logs:read permission"""
    return AuditLogService.get_entity_history(db, entity_type, entity_id, page, limit)


@router.get("/me/activity", response_model=AuditLogWithPagination)
def get_my_activity(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=200, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get current user's activity logs"""
    return AuditLogService.get_user_activity(db, current_user.id, page, limit)
