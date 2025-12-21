"""
Coupon Reward Router

API endpoints for managing coupon reward rules and user coupons.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.coupon_reward import (
    CouponRewardRuleCreate,
    CouponRewardRuleUpdate,
    CouponRewardRuleResponse,
    CouponRewardRuleListResponse,
    UserCouponResponse,
    UserCouponListResponse,
    CouponValidationResponse,
    PublicCouponCreate,
    PublicCouponUpdate
)
from app.services.coupon_reward_service import CouponRewardService
from app.deps.auth import require_permission, get_current_active_user
from app.models.user import User

router = APIRouter()


# ==================== Admin: Reward Rule Management ====================

@router.post(
    "/reward-rules",
    response_model=CouponRewardRuleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new coupon reward rule"
)
def create_reward_rule(
    rule_data: CouponRewardRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["coupon_rules:create"]))
):
    """
    Create a new coupon reward rule.
    
    **Trigger Types:**
    - `order_amount`: Generate coupon when order total >= threshold_amount
    - `order_count`: Generate coupon when user's order count >= threshold_count
    
    **Permissions:** `coupon_rules:create`
    """
    return CouponRewardService.create_rule(db=db, rule_data=rule_data)


@router.get(
    "/reward-rules",
    response_model=CouponRewardRuleListResponse,
    summary="List all coupon reward rules"
)
def list_reward_rules(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["coupon_rules:read"]))
):
    """
    List all coupon reward rules with optional filtering.
    
    **Permissions:** `coupon_rules:read`
    """
    rules, total = CouponRewardService.get_rules(
        db=db, skip=skip, limit=limit, is_active=is_active
    )
    return {
        "rules": rules,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get(
    "/reward-rules/{rule_id}",
    response_model=CouponRewardRuleResponse,
    summary="Get a specific reward rule"
)
def get_reward_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["coupon_rules:read"]))
):
    """
    Get details of a specific coupon reward rule.
    
    **Permissions:** `coupon_rules:read`
    """
    return CouponRewardService.get_rule_by_id(db=db, rule_id=rule_id)


@router.put(
    "/reward-rules/{rule_id}",
    response_model=CouponRewardRuleResponse,
    summary="Update a reward rule"
)
def update_reward_rule(
    rule_id: int,
    rule_update: CouponRewardRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["coupon_rules:update"]))
):
    """
    Update an existing coupon reward rule.
    
    **Permissions:** `coupon_rules:update`
    """
    return CouponRewardService.update_rule(db=db, rule_id=rule_id, rule_update=rule_update)


@router.delete(
    "/reward-rules/{rule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a reward rule"
)
def delete_reward_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["coupon_rules:delete"]))
):
    """
    Delete a coupon reward rule.
    
    **Permissions:** `coupon_rules:delete`
    """
    CouponRewardService.delete_rule(db=db, rule_id=rule_id)


# ==================== Admin: Public Coupon (Promo Code) Management ====================

@router.post(
    "/public",
    response_model=UserCouponResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a public promo code"
)
def create_public_coupon(
    coupon_data: PublicCouponCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["coupon_rules:create"]))
):
    """
    Create a public promo code that any customer can use.
    
    Example: SUMMER2024, BLACKFRIDAY, WELCOME10
    
    **Permissions:** `coupon_rules:create`
    """
    return CouponRewardService.create_public_coupon(
        db=db,
        name=coupon_data.name,
        description=coupon_data.description,
        discount_type=coupon_data.discount_type.value,
        discount_value=float(coupon_data.discount_value),
        minimum_order_amount=float(coupon_data.minimum_order_amount) if coupon_data.minimum_order_amount else None,
        maximum_discount_amount=float(coupon_data.maximum_discount_amount) if coupon_data.maximum_discount_amount else None,
        valid_from=coupon_data.valid_from,
        valid_until=coupon_data.valid_until,
        usage_limit=coupon_data.usage_limit
    )


@router.get(
    "/public",
    response_model=UserCouponListResponse,
    summary="List all public promo codes"
)
def list_public_coupons(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    include_expired: bool = Query(False, description="Include expired coupons"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["coupon_rules:read"]))
):
    """
    List all public promo codes.
    
    **Permissions:** `coupon_rules:read`
    """
    coupons, total = CouponRewardService.get_public_coupons(
        db=db, skip=skip, limit=limit, include_expired=include_expired
    )
    return {
        "coupons": coupons,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.put(
    "/public/{coupon_id}",
    response_model=UserCouponResponse,
    summary="Update a public promo code"
)
def update_public_coupon(
    coupon_id: int,
    coupon_update: PublicCouponUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["coupon_rules:update"]))
):
    """
    Update an existing public promo code.
    
    **Permissions:** `coupon_rules:update`
    """
    return CouponRewardService.update_public_coupon(
        db=db,
        coupon_id=coupon_id,
        update_data=coupon_update.model_dump(exclude_unset=True)
    )


@router.delete(
    "/public/{coupon_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a public promo code"
)
def delete_public_coupon(
    coupon_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["coupon_rules:delete"]))
):
    """
    Delete a public promo code.
    
    **Permissions:** `coupon_rules:delete`
    """
    CouponRewardService.delete_public_coupon(db=db, coupon_id=coupon_id)


# ==================== Customer: My Coupons ====================

@router.get(
    "/my-coupons",
    response_model=UserCouponListResponse,
    summary="Get my coupons"
)
def get_my_coupons(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    include_used: bool = Query(False, description="Include used coupons"),
    include_expired: bool = Query(False, description="Include expired coupons"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all coupons for the current user.
    
    By default, only shows valid unused coupons.
    """
    coupons, total = CouponRewardService.get_user_coupons(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        include_used=include_used,
        include_expired=include_expired
    )
    return {
        "coupons": coupons,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get(
    "/validate/{coupon_code}",
    response_model=CouponValidationResponse,
    summary="Validate a coupon code"
)
def validate_coupon_code(
    coupon_code: str,
    order_amount: float = Query(..., gt=0, description="Order amount to validate against"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Validate a coupon code before checkout.
    
    Works with both personal coupons and public promo codes.
    
    Returns coupon details if valid, or error message if not.
    """
    try:
        coupon = CouponRewardService.validate_coupon(
            db=db,
            coupon_code=coupon_code,
            user_id=current_user.id,
            order_amount=order_amount
        )
        
        discount_amount = coupon.calculate_discount_amount(order_amount)
        
        return {
            "is_valid": True,
            "code": coupon.code,
            "discount_type": coupon.discount_type,
            "discount_value": coupon.discount_value,
            "minimum_order_amount": coupon.minimum_order_amount,
            "maximum_discount_amount": coupon.maximum_discount_amount,
            "valid_until": coupon.valid_until,
            "message": f"Coupon is valid! You'll save ${discount_amount:.2f}"
        }
    except Exception as e:
        return {
            "is_valid": False,
            "code": coupon_code,
            "message": str(e.detail) if hasattr(e, 'detail') else str(e)
        }


# ==================== Admin: View All User Coupons ====================

@router.get(
    "/admin/user-coupons",
    response_model=UserCouponListResponse,
    summary="Admin: List all user coupons"
)
def admin_list_all_coupons(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    is_used: Optional[bool] = Query(None, description="Filter by usage status"),
    is_public: Optional[bool] = Query(None, description="Filter by public status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["coupon_rules:read"]))
):
    """
    Admin endpoint to view all user coupons with filtering.
    
    **Permissions:** `coupon_rules:read`
    """
    from app.models.user_coupon import UserCoupon
    
    query = db.query(UserCoupon)
    
    if user_id:
        query = query.filter(UserCoupon.user_id == user_id)
    if is_used is not None:
        query = query.filter(UserCoupon.is_used == is_used)
    if is_public is not None:
        query = query.filter(UserCoupon.is_public == is_public)
    
    total = query.count()
    coupons = query.order_by(UserCoupon.created_at.desc()).offset(skip).limit(limit).all()
    
    return {
        "coupons": coupons,
        "total": total,
        "skip": skip,
        "limit": limit
    }

