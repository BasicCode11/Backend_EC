from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from app.models.team import Team
from app.models.user import User
from app.schemas.team import TeamCreate, TeamUpdate

class TeamService:
    
    @staticmethod
    def get_accessible_teams(db: Session, current_user: User) -> List[Team]:
        if not current_user.team_id:
            if not current_user.role or current_user.role.lower() != "super admin":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to view teams"
                )
            #if user role == super admin show all team 
            return db.query(Team).all()
        
        if current_user.role and current_user.role.name.lower() == "super admin":
            # Super admin with a team can still see all
            return db.query(Team).all()
        
        # Regular user: only see their own team
        team = db.query(Team).filter(Team.id == current_user.team_id).first()
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found"
            )
        return [team]
        
        
    @staticmethod
    def get_by_name(db: Session, team_name: str)-> Optional[Team]:
        return db.query(Team).filter(Team.team_name == team_name).first()
    
    
    @staticmethod
    def create(db: Session, team_data: TeamCreate, current_user: User) -> Team:
        """
        Create a team.
        Only users with role 'super admin' can create a team.
        """
        if not current_user.role or current_user.role.name.lower() != "super admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only super admin users can create teams"
            )
        team = Team(
            team_name=team_data.team_name,
            team_logo=team_data.team_logo,
            description=team_data.description,
            create_by=current_user.id
        )
        db.add(team)
        db.commit()
        db.refresh(team)
        return {
            "message": "Team created successfully",
            "data": team
        }
    
    @staticmethod
    def update(db: Session, team_id: int, team_data: TeamUpdate , current_user: User) -> Optional[Team]:
        """
        Update a team. Only super admin can update any team.
        """
        if not current_user.role or current_user.role.name.lower() != "super admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only super admin users can update teams"
            )
        
        team = db.query(Team).filter(Team.id == team_id).first()
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        
        team.update_team_info(
            team_name=team_data.team_name,
            team_logo=team_data.team_logo,
            description=team_data.description
        )
        
        
        db.commit()
        db.refresh(team)
        return {
            "message": "Team updated successfully",
            "data": team
        }
    

    @staticmethod
    def delete(db: Session, team_id: int , current_user: User) -> bool:
        """
        Delete a team. Only super admin can update any team.
        """
        if not current_user.role or current_user.role.name.lower() != "super admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only super admin users can update teams"
            )
        
        team = db.query(Team).filter(Team.id == team_id).first()
        
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        
        db.delete(team)
        db.commit()
        return {"detail": "Team deleted successfully"}
    

    @staticmethod
    def search_teams(db: Session, query: str, limit: int = 10) -> List[Team]:
        return TeamService.db.query(Team).filter(
            Team.team_name.ilike(f"%{query}%")
        ).limit(limit).all()