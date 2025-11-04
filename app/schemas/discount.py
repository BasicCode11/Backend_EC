from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from decimal import Decimal
from enum import Enum


class DiscountType(str, Enum):
    PERCENTAGE = "percentage"
    FIXED_AMOUNT = "fixed_amount"


class ApplyTo(str, Enum):
    ORDER = "order"
    PRODUCT = "product"
    CATEGORY = "category"


class DiscountBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    discount_type: DiscountType
    discount_value: Decimal = Field(..., gt=0, description="Percentage (0-100) or fixed amount")
    minimum_order_amount: Optional[Decimal] = Field(None, ge=0)
    maximum_discount_amount: Optional[Decimal] = Field(None, ge=0)
    usage_limit: Optional[int] = Field(None, ge=1)
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    is_active: bool = True
    apply_to: ApplyTo = ApplyTo.ORDER

    @field_validator('discount_value')
    @classmethod
    def validate_discount_value(cls, v, info):
        if info.data.get('discount_type') == DiscountType.PERCENTAGE and v > 100:
            raise ValueError('Percentage discount cannot exceed 100%')
        return v


class DiscountCreate(DiscountBase):
    pass


class DiscountUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    discount_type: Optional[DiscountType] = None
    discount_value: Optional[Decimal] = Field(None, gt=0)
    minimum_order_amount: Optional[Decimal] = Field(None, ge=0)
    maximum_discount_amount: Optional[Decimal] = Field(None, ge=0)
    usage_limit: Optional[int] = Field(None, ge=1)
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    is_active: Optional[bool] = None
    apply_to: Optional[ApplyTo] = None


class DiscountResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    discount_type: str
    discount_value: Decimal
    minimum_order_amount: Optional[Decimal] = None
    maximum_discount_amount: Optional[Decimal] = None
    usage_limit: Optional[int] = None
    used_count: int
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    is_active: bool
    apply_to: str
    is_valid: bool = False
    remaining_usage: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
