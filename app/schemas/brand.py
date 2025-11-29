from pydantic import BaseModel, Field
from typing import Optional
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


class BrandResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    logo: str
    logo_public_id: str
    status: str
    created_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BrandWithProducts(BrandResponse):
    product_count: int = 0

    class Config:
        from_attributes = True
