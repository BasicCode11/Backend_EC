from fastapi import HTTPException, status , Depends
from app.models.team import Team
from app.models.user import User
from app.deps.user import get_current_active_user
from sqlalchemy.orm import Session
from app.database import get_db



def can_manage_team(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Team:
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    if current_user.role.name.lower() == "super admin":
        return team
    if current_user.team_id == team_id:
        return team
    if team.create_by == current_user.id:
        return team
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Cannot manage this team"
    )

def can_view_team(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Team:
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    if current_user.role.name.lower() == "super admin":
        return team
    if current_user.team_id == team_id:
        return team
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Cannot view this team"
    )