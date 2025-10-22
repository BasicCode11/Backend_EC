from typing import List , Optional
from fastapi import Depends, HTTPException, status , Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.database import get_db
from app.models.user import User
from app.core.security import decode_access_token, TokenData
from app.core.config import settings
from app.core.exceptions import (
    ForbiddenException,
    InvalidTokenException,
    TeamAccessDeniedException,
    AgentAccessDeniedException,
)

security = HTTPBearer()


# CURRENT USER 
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    response: Response = None,  # allow setting headers
) -> User:
    token = credentials.credentials
    token_data = decode_access_token(token)

    user = db.query(User).filter(User.email == token_data.sub).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not user.email_verified:
        raise ForbiddenException("Email not verified")

    # Enforce idle timeout (customers)
    role_name = user.role.name if user.role else None
    if role_name == "customer":
        last_seen = user.last_login_at or user.updated_at or user.created_at
        now = datetime.now(timezone.utc)
        if last_seen and (now - last_seen) > settings.customer_idle_timeout:
            raise InvalidTokenException("Session expired due to inactivity")
        user.last_login_at = now
        db.add(user)
        db.commit()

        # Auto-refresh if expiring soon (e.g., < 2 hours)
    try:
        exp_dt = datetime.fromtimestamp(token_data.exp, tz=timezone.utc)
        if exp_dt - datetime.now(timezone.utc) < timedelta(hours=2):
            new_token = AuthService.create_user_access_token(user)
            if response is not None:
                response.headers["X-New-Token"] = new_token
    except Exception:
        pass

    return user


#  ACTIVE USER 
def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.email_verified:
        raise HTTPException(status_code=400, detail="Email not verified")
    return current_user


# ROLE CHECK
def require_roles(allowed_roles: List[str]):
    """Check if user role is allowed"""
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if not current_user.role:
            raise ForbiddenException("User has no role assigned")
        if current_user.role.name not in allowed_roles:
            raise ForbiddenException("You do not have access to this resource")
        return current_user
    return role_checker

def require_super_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """Check if user is a super admin"""
    if not current_user.role or current_user.role.name != "super admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required"
        )
    return current_user
# PERMISSION CHECK 
def require_permission(required_permissions: List[str]):
    """Check if user has required permissions"""
    def permission_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if not current_user.role:
            raise ForbiddenException("User has no role assigned")

        permissions = current_user.role.get_permission_names()
        if not set(required_permissions).issubset(permissions):
            raise ForbiddenException("You do not have required permissions")

        return current_user
    return permission_checker


#  TEAM CHECK 
def require_team_access(resource_team_id: int):
    """Check if the resource belongs to user's team"""
    def team_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if not current_user.team_id or current_user.team_id != resource_team_id:
            raise TeamAccessDeniedException(
                f"Resource belongs to team {resource_team_id}, but you are in team {current_user.team_id}"
            )
        return current_user
    return team_checker


#  AGENT CHECK 
def require_agent_access(resource_agent_id: int):
    """Check if the resource belongs to user's agent"""
    def agent_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if not current_user.agent_id or current_user.agent_id != resource_agent_id:
            raise AgentAccessDeniedException(
                f"Resource belongs to agent {resource_agent_id}, but you are under agent {current_user.agent_id}"
            )
        return current_user
    return agent_checker


# TEAM + AGENT CHECK
def require_team_and_agent(resource_team_id: int, resource_agent_id: int):
    """Check both team and agent access"""
    def checker(current_user: User = Depends(get_current_active_user)) -> User:
        if not current_user.team_id or current_user.team_id != resource_team_id:
            raise TeamAccessDeniedException(
                f"Resource belongs to team {resource_team_id}, but you are in team {current_user.team_id}"
            )
        if not current_user.agent_id or current_user.agent_id != resource_agent_id:
            raise AgentAccessDeniedException(
                f"Resource belongs to agent {resource_agent_id}, but you are under agent {current_user.agent_id}"
            )
        return current_user
    return checker
