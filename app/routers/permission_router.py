from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from ..deps.permission import check_permissions
from ..services.permission_service import PermissionService
from app.schemas.role import PermissionOut

router = APIRouter()

@router.get("/permissions", response_model=List[PermissionOut])
def list_permissions(
    db: Session = Depends(get_db),
    _: bool = Depends(check_permissions(["permissions:read"])),
) -> List[PermissionOut]:
    """List all permissions. Requires permissions:read permission."""
    permissions = PermissionService.get_all(db)
    print(f"Permissions: {permissions}")
    return permissions