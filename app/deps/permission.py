from typing import List
from fastapi import Depends, HTTPException, status
from app.models.user import User
from app.deps.auth import get_current_user

def check_permissions(required_permissions: List[str]):
    async def permission_checker(
        current_user: User = Depends(get_current_user)
    ) -> User:
        if not current_user.role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no role assigned"
            )

        # Get all permissions including inherited ones from role hierarchy
        user_permissions = set(current_user.role.get_permission_names())

        if not all(perm in user_permissions for perm in required_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions. Required: {', '.join(required_permissions)}"
            )
        return current_user
    return permission_checker
