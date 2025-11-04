from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ReviewBase(BaseModel):
    product_id: int
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    title: Optional[str] = Field(None, max_length=255)
    comment: Optional[str] = None
    order_id: Optional[int] = None


class ReviewCreate(BaseModel):
    product_id: int
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    title: Optional[str] = Field(None, max_length=255)
    comment: Optional[str] = None


class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    title: Optional[str] = Field(None, max_length=255)
    comment: Optional[str] = None


class ReviewApprovalUpdate(BaseModel):
    is_approved: bool


class ReviewResponse(BaseModel):
    id: int
    product_id: int
    user_id: int
    order_id: Optional[int] = None
    rating: int
    title: Optional[str] = None
    comment: Optional[str] = None
    is_approved: bool
    helpful_count: int
    is_verified_purchase: bool = False
    user_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReviewListResponse(BaseModel):
    items: list[ReviewResponse]
    total: int
    page: int
    limit: int
    pages: int
    average_rating: Optional[float] = None
