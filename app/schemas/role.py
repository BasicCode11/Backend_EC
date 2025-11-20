from pydantic import BaseModel, field_validator
from typing import Optional ,List
from app.utils.validation import RoleValidation
from datetime import datetime


class PermissionOut(BaseModel):
    id: int
    name: str
    class Config:
        from_attributes = True


class RoleOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    permissions: List[PermissionOut] = []

    class Config:
        from_attributes = True


class RoleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    permission_ids: List[int] = []  # ✅ allow assigning permissions when creating

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return RoleValidation.validate_role_name(v)

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return RoleValidation.validate_description(v)
        return v


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permission_ids: Optional[List[int]] = None  # ✅ allow re-assigning permissions

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return RoleValidation.validate_role_name(v)
        return v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return RoleValidation.validate_description(v)
        return v
    
class RolePermissionAssignment(BaseModel):
    permission_ids: List[int]