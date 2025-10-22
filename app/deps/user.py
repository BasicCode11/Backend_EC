from fastapi import Depends, HTTPException, status
from app.models.user import User
from app.deps.auth import get_current_active_user



# Role-based dependencies
def require_super_admin(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Only Super Admin can pass"""
    if current_user.role.name != "super admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super Admin access required",
        )
    return current_user


def require_team_user(
    resource_team_id: int,
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Team-level user can only control resources inside their own team.
    Super Admin bypasses this check.
    """
    if current_user.role.name == "super admin":
        return current_user

    if not current_user.team_id or current_user.team_id != resource_team_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to your own team",
        )
    return current_user


def require_agent_user(
    resource_agent_id: int,
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Agent-level user can only control resources assigned to their own agent.
    Super Admin bypasses this check.
    """
    if current_user.role.name == "super admin":
        return current_user

    if not current_user.agent_id or current_user.agent_id != resource_agent_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to your own agent",
        )
    return current_user


def can_assign_agent(
    target_agent_id: int,
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Check if user can assign agents"""
    # Super admin can assign any agent
    if current_user.role.name == "super admin":
        return current_user
        
    # Admin/User can only assign agents in their team
    # You might want to add additional logic here based on your business rules
    return current_user