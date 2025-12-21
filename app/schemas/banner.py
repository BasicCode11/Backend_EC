from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class BannerBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    status: Optional[str] = Field(default="open", pattern="^(open|closed)$")
    slug: Optional[str] = Field(None, min_length=1, max_length=100)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class BannerCreate(BannerBase):
    pass

class BannerUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    status: Optional[str] = Field(None, pattern="^(open|closed)$")
    slug: Optional[str] = Field(None, min_length=1, max_length=100)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class UserSimple(BaseModel):
    id: int
    first_name: str
    last_name: str

    class Config:
        from_attributes = True

class BannerResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    image: str
    image_public_id: str
    status: str
    slug: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    created_by: int
    user: UserSimple
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True



class BannerListResponse(BaseModel):
    banners: List[BannerResponse]
    total: int
    page: int
    limit: int