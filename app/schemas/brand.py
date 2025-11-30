from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class BrandBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    status: str = Field(default="active", pattern="^(active|inactive)$")


class BrandCreate(BrandBase):
    pass


class BrandUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    status: Optional[str] = Field(None, pattern="^(active|inactive)$")

class UserSimple(BaseModel):
    id: int
    first_name: str
    last_name: str

    class Config:
        from_attributes = True


class BrandResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    logo: str
    logo_public_id: str
    status: str
    user: UserSimple = Field(..., serialization_alias="created_by")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BrandListResponse(BaseModel):
    """Response schema for paginated brand list"""
    brands: List[BrandResponse]
    total: int
    page: int
    limit: int
    pages: int


class BrandWithProducts(BrandResponse):
    product_count: int = 0

    class Config:
        from_attributes = True
