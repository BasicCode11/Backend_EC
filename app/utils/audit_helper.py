"""
Helper functions for audit logging
"""
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import Request

from app.services.audit_log_service import AuditLogService


def get_client_info(request: Request) -> tuple[Optional[str], Optional[str]]:
    """Extract IP address and user agent from request"""
    ip_address = None
    user_agent = None
    
    if request:
        # Get IP address (consider proxy headers)
        ip_address = (
            request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
            or request.headers.get("X-Real-IP", "")
            or request.client.host if request.client else None
        )
        
        # Get user agent
        user_agent = request.headers.get("User-Agent")
    
    return ip_address, user_agent


def log_user_create(
    db: Session,
    user_id: Optional[int],
    created_user_id: int,
    created_user_uuid: str,
    request: Optional[Request] = None
):
    """Log user creation action"""
    ip_address, user_agent = get_client_info(request) if request else (None, None)
    
    AuditLogService.log_create(
        db=db,
        user_id=user_id,
        entity_type="User",
        entity_id=created_user_id,
        entity_uuid=created_user_uuid,
        ip_address=ip_address,
        user_agent=user_agent
    )


def log_user_update(
    db: Session,
    user_id: Optional[int],
    updated_user_id: int,
    updated_user_uuid: str,
    old_values: Optional[Dict[str, Any]] = None,
    new_values: Optional[Dict[str, Any]] = None,
    changes: Optional[Dict[str, Any]] = None,
    request: Optional[Request] = None
):
    """Log user update action"""
    ip_address, user_agent = get_client_info(request) if request else (None, None)
    
    AuditLogService.log_update(
        db=db,
        user_id=user_id,
        entity_type="User",
        entity_id=updated_user_id,
        entity_uuid=updated_user_uuid,
        old_values=old_values,
        new_values=new_values,
        changes=changes,
        ip_address=ip_address,
        user_agent=user_agent
    )


def log_user_delete(
    db: Session,
    user_id: Optional[int],
    deleted_user_id: int,
    deleted_user_uuid: str,
    old_values: Optional[Dict[str, Any]] = None,
    request: Optional[Request] = None
):
    """Log user deletion action"""
    ip_address, user_agent = get_client_info(request) if request else (None, None)
    
    AuditLogService.log_delete(
        db=db,
        user_id=user_id,
        entity_type="User",
        entity_id=deleted_user_id,
        entity_uuid=deleted_user_uuid,
        old_values=old_values,
        ip_address=ip_address,
        user_agent=user_agent
    )


def log_login(
    db: Session,
    user_id: int,
    success: bool = True,
    request: Optional[Request] = None
):
    """Log user login attempt"""
    ip_address, user_agent = get_client_info(request) if request else (None, None)
    
    AuditLogService.log_login(
        db=db,
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
        success=success
    )


def log_logout(
    db: Session,
    user_id: int,
    request: Optional[Request] = None
):
    """Log user logout"""
    ip_address, user_agent = get_client_info(request) if request else (None, None)
    
    AuditLogService.log_logout(
        db=db,
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent
    )


def log_entity_action(
    db: Session,
    action: str,
    entity_type: str,
    entity_id: int,
    user_id: Optional[int] = None,
    entity_uuid: Optional[str] = None,
    old_values: Optional[Dict[str, Any]] = None,
    new_values: Optional[Dict[str, Any]] = None,
    changes: Optional[Dict[str, Any]] = None,
    description: Optional[str] = None,
    request: Optional[Request] = None
):
    """Generic function to log any entity action"""
    ip_address, user_agent = get_client_info(request) if request else (None, None)
    
    AuditLogService.create_log(
        db=db,
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        entity_uuid=entity_uuid,
        old_values=old_values,
        new_values=new_values,
        changes=changes,
        ip_address=ip_address,
        user_agent=user_agent,
        description=description
    )
