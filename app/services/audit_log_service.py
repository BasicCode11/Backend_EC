from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_
from datetime import datetime

from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.audit_log import (
    AuditLogCreate,
    AuditLogFilter,
    AuditLogWithUser,
    AuditLogWithPagination
)


class AuditLogService:
    """Service layer for audit log operations."""

    @staticmethod
    def create_log(
        db: Session,
        user_id: Optional[int],
        action: str,
        entity_type: str,
        entity_id: Optional[int] = None,
        entity_uuid: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        description: Optional[str] = None
    ) -> AuditLog:
        """Create a new audit log entry"""
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_uuid=entity_uuid,
            changes=changes,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent,
            description=description
        )
        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)
        return audit_log

    @staticmethod
    def log_create(
        db: Session,
        user_id: Optional[int],
        entity_type: str,
        entity_id: int,
        entity_uuid: Optional[str] = None,
        new_values: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """Convenience method for logging create actions"""
        return AuditLogService.create_log(
            db=db,
            user_id=user_id,
            action="CREATE",
            entity_type=entity_type,
            entity_id=entity_id,
            entity_uuid=entity_uuid,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent,
            description=f"Created {entity_type} with ID {entity_id}"
        )

    @staticmethod
    def log_update(
        db: Session,
        user_id: Optional[int],
        entity_type: str,
        entity_id: int,
        entity_uuid: Optional[str] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        changes: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """Convenience method for logging update actions"""
        return AuditLogService.create_log(
            db=db,
            user_id=user_id,
            action="UPDATE",
            entity_type=entity_type,
            entity_id=entity_id,
            entity_uuid=entity_uuid,
            old_values=old_values,
            new_values=new_values,
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent,
            description=f"Updated {entity_type} with ID {entity_id}"
        )

    @staticmethod
    def log_delete(
        db: Session,
        user_id: Optional[int],
        entity_type: str,
        entity_id: int,
        entity_uuid: Optional[str] = None,
        old_values: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """Convenience method for logging delete actions"""
        return AuditLogService.create_log(
            db=db,
            user_id=user_id,
            action="DELETE",
            entity_type=entity_type,
            entity_id=entity_id,
            entity_uuid=entity_uuid,
            old_values=old_values,
            ip_address=ip_address,
            user_agent=user_agent,
            description=f"Deleted {entity_type} with ID {entity_id}"
        )

    @staticmethod
    def log_login(
        db: Session,
        user_id: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True
    ) -> AuditLog:
        """Log user login attempts"""
        action = "LOGIN_SUCCESS" if success else "LOGIN_FAILED"
        return AuditLogService.create_log(
            db=db,
            user_id=user_id if success else None,
            action=action,
            entity_type="User",
            entity_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            description=f"User login {'successful' if success else 'failed'}"
        )

    @staticmethod
    def log_logout(
        db: Session,
        user_id: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """Log user logout"""
        return AuditLogService.create_log(
            db=db,
            user_id=user_id,
            action="LOGOUT",
            entity_type="User",
            entity_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            description="User logged out"
        )

    @staticmethod
    def get_all(
        db: Session,
        filters: AuditLogFilter
    ) -> AuditLogWithPagination:
        """Get audit logs with filters and pagination"""
        query = db.query(AuditLog)

        # Apply filters
        if filters.user_id:
            query = query.filter(AuditLog.user_id == filters.user_id)
        
        if filters.action:
            query = query.filter(AuditLog.action == filters.action)
        
        if filters.entity_type:
            query = query.filter(AuditLog.entity_type == filters.entity_type)
        
        if filters.entity_id:
            query = query.filter(AuditLog.entity_id == filters.entity_id)
        
        if filters.entity_uuid:
            query = query.filter(AuditLog.entity_uuid == filters.entity_uuid)
        
        if filters.start_date:
            query = query.filter(AuditLog.created_at >= filters.start_date)
        
        if filters.end_date:
            query = query.filter(AuditLog.created_at <= filters.end_date)

        # Get total count
        total = query.count()

        # Apply pagination and ordering
        logs = query.order_by(AuditLog.created_at.desc())\
            .offset((filters.page - 1) * filters.limit)\
            .limit(filters.limit)\
            .all()

        # Transform to response format with user info
        items = []
        for log in logs:
            log_dict = {
                "id": log.id,
                "user_id": log.user_id,
                "action": log.action,
                "entity_type": log.entity_type,
                "entity_id": log.entity_id,
                "entity_uuid": log.entity_uuid,
                "changes": log.changes,
                "old_values": log.old_values,
                "new_values": log.new_values,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "description": log.description,
                "created_at": log.created_at,
                "user_email": log.user.email if log.user else None,
                "user_name": log.user.full_name if log.user else None
            }
            items.append(AuditLogWithUser(**log_dict))

        return AuditLogWithPagination(
            items=items,
            total=total,
            page=filters.page,
            limit=filters.limit
        )

    @staticmethod
    def get_by_id(db: Session, log_id: int) -> Optional[AuditLog]:
        """Get audit log by ID"""
        return db.get(AuditLog, log_id)

    @staticmethod
    def get_user_activity(
        db: Session,
        user_id: int,
        page: int = 1,
        limit: int = 50
    ) -> AuditLogWithPagination:
        """Get all activity logs for a specific user"""
        filters = AuditLogFilter(
            user_id=user_id,
            page=page,
            limit=limit
        )
        return AuditLogService.get_all(db, filters)

    @staticmethod
    def get_entity_history(
        db: Session,
        entity_type: str,
        entity_id: int,
        page: int = 1,
        limit: int = 50
    ) -> AuditLogWithPagination:
        """Get all audit logs for a specific entity"""
        filters = AuditLogFilter(
            entity_type=entity_type,
            entity_id=entity_id,
            page=page,
            limit=limit
        )
        return AuditLogService.get_all(db, filters)
