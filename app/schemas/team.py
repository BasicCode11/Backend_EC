from typing import Optional
from datetime import datetime, timezone
from decimal import Decimal
from pydantic import BaseModel, Field

class TeamBase(BaseModel):
    team_name: str
    team_logo: Optional[str] = None
    description: Optional[str] = None

class TeamCreate(TeamBase):
    pass

class TeamUpdate(BaseModel):
    team_name: Optional[str] = None
    team_logo: Optional[str] = None
    description: Optional[str] = None



class TeamResponse(TeamBase):
    id: int
    created_at: datetime
    updated_at: datetime
    user_count: int = Field(0, description="Number of users in the team")
    has_logo: bool = Field(False, description="Indicates if the team has a logo")

    class Config:
        from_attributes = True

class TeamWithUsers(TeamResponse):
    users: list["UserSimple"] = []

class UserSimple(BaseModel):
    id: int
    username: str
    status: bool

    class Config:
        from_attributes = True