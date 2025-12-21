
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal
from enum import Enum


class RewardTriggerType(str, Enum):
    ORDER_AMOUNT = "order_amount"
    ORDER_COUNT = "order_count"


class CouponDiscountType(str, Enum):
    PERCENTAGE = "percentage"
    FIXED_AMOUNT = "fixed_amount"


# ==================== Coupon Reward Rule Schemas ====================

class CouponRewardRuleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    trigger_type: RewardTriggerType
    threshold_amount: Optional[Decimal] = Field(None, ge=0, description="Min order amount to trigger")
    threshold_count: Optional[int] = Field(None, ge=1, description="Number of orders to trigger")
    coupon_discount_type: CouponDiscountType
    coupon_discount_value: Decimal = Field(..., gt=0)
    coupon_minimum_order: Optional[Decimal] = Field(None, ge=0)
    coupon_maximum_discount: Optional[Decimal] = Field(None, ge=0)
    coupon_valid_days: int = Field(default=30, ge=1, le=365)
    is_active: bool = True
    is_one_time: bool = False
    priority: int = Field(default=0, ge=0)


class CouponRewardRuleCreate(CouponRewardRuleBase):
    pass


class CouponRewardRuleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    trigger_type: Optional[RewardTriggerType] = None
    threshold_amount: Optional[Decimal] = Field(None, ge=0)
    threshold_count: Optional[int] = Field(None, ge=1)
    coupon_discount_type: Optional[CouponDiscountType] = None
    coupon_discount_value: Optional[Decimal] = Field(None, gt=0)
    coupon_minimum_order: Optional[Decimal] = Field(None, ge=0)
    coupon_maximum_discount: Optional[Decimal] = Field(None, ge=0)
    coupon_valid_days: Optional[int] = Field(None, ge=1, le=365)
    is_active: Optional[bool] = None
    is_one_time: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=0)


class CouponRewardRuleResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    trigger_type: str
    threshold_amount: Optional[Decimal] = None
    threshold_count: Optional[int] = None
    coupon_discount_type: str
    coupon_discount_value: Decimal
    coupon_minimum_order: Optional[Decimal] = None
    coupon_maximum_discount: Optional[Decimal] = None
    coupon_valid_days: int
    is_active: bool
    is_one_time: bool
    priority: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CouponRewardRuleListResponse(BaseModel):
    rules: list[CouponRewardRuleResponse]
    total: int
    skip: int
    limit: int


# ==================== User Coupon Schemas ====================

class UserCouponResponse(BaseModel):
    id: int
    code: str
    user_id: Optional[int] = None
    reward_rule_id: Optional[int] = None
    triggered_by_order_id: Optional[int] = None
    discount_type: str
    discount_value: Decimal
    minimum_order_amount: Optional[Decimal] = None
    maximum_discount_amount: Optional[Decimal] = None
    valid_from: datetime
    valid_until: datetime
    is_used: bool
    used_at: Optional[datetime] = None
    used_on_order_id: Optional[int] = None
    email_sent: bool
    email_sent_at: Optional[datetime] = None
    # New public coupon fields
    is_public: bool = False
    name: Optional[str] = None
    description: Optional[str] = None
    usage_limit: Optional[int] = None
    usage_count: int = 0
    is_valid: bool = False
    is_expired: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class UserCouponListResponse(BaseModel):
    coupons: list[UserCouponResponse]
    total: int
    skip: int
    limit: int


class ApplyCouponRequest(BaseModel):
    """Request to apply a user coupon at checkout"""
    coupon_code: str = Field(..., min_length=1, max_length=50)


class CouponValidationResponse(BaseModel):
    """Response after validating a coupon code"""
    is_valid: bool
    code: str
    discount_type: Optional[str] = None
    discount_value: Optional[Decimal] = None
    minimum_order_amount: Optional[Decimal] = None
    maximum_discount_amount: Optional[Decimal] = None
    valid_until: Optional[datetime] = None
    message: str


# ==================== Public Coupon (Promo Code) Schemas ====================

class PublicCouponCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Display name")
    description: Optional[str] = Field(None, max_length=500)    
    discount_type: CouponDiscountType
    discount_value: Decimal = Field(..., gt=0)
    minimum_order_amount: Optional[Decimal] = Field(None, ge=0)
    maximum_discount_amount: Optional[Decimal] = Field(None, ge=0)
    valid_from: Optional[datetime] = None
    valid_until: datetime = Field(..., description="Expiry date")
    usage_limit: Optional[int] = Field(None, ge=1, description="Max number of uses")


class PublicCouponUpdate(BaseModel):
    """Schema for updating a public promo code"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    discount_type: Optional[CouponDiscountType] = None
    discount_value: Optional[Decimal] = Field(None, gt=0)
    minimum_order_amount: Optional[Decimal] = Field(None, ge=0)
    maximum_discount_amount: Optional[Decimal] = Field(None, ge=0)
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    usage_limit: Optional[int] = Field(None, ge=1)

