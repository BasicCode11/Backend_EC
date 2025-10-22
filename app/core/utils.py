
from sqlalchemy.orm import Session
from app.models import User, Role, Permission  
from fastapi import HTTPException, status


# --------------------------
# RBAC / Permission Helpers
# --------------------------
def has_permission(user: User, permission_name: str, db: Session) -> bool:
    """
    Check if a user has a specific permission via their role.
    """
    role = db.query(Role).filter(Role.id == user.role_id).first()
    if not role:
        return False

    permission = (
        db.query(Permission)
        .join(Role.permissions)  # Assumes Role has a relationship "permissions"
        .filter(Permission.name == permission_name)
        .first()
    )
    return permission is not None


def require_permission(user: User, permission_name: str, db: Session):
    """
    Raises HTTPException if user does not have the required permission.
    """
    if not has_permission(user, permission_name, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission '{permission_name}' required"
        )


def has_role(user: User, *role_names: str) -> bool:
    """
    Check if the user's role matches any of the provided role names.
    """
    return user.role.name in role_names if user.role else False


def require_role(user: User, *role_names: str):
    """
    Raises HTTPException if user does not have one of the required roles.
    """
    if not has_role(user, *role_names):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User role must be one of {role_names}"
        )
