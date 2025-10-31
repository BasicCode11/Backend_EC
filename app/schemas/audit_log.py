from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class AuditLogBase(BaseModel):
    action: str
    entity_type: str
    entity_id: Optional[int] = None
    entity_uuid: Optional[str] = None
    changes: Optional[Dict[str, Any]] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    description: Optional[str] = None


class AuditLogCreate(AuditLogBase):
    user_id: Optional[int] = None


class AuditLogResponse(AuditLogBase):
    id: int
    user_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogWithUser(AuditLogResponse):
    user_email: Optional[str] = None
    user_name: Optional[str] = None


class AuditLogFilter(BaseModel):
    user_id: Optional[int] = None
    action: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    entity_uuid: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=50, ge=1, le=200)


class AuditLogWithPagination(BaseModel):
    items: list[AuditLogWithUser]
    total: int
    page: int
    limit: int
    
    class Config:
        from_attributes = True
