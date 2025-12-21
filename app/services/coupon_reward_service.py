
from typing import List, Optional, Tuple
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from fastapi import HTTPException, status

from app.models.coupon_reward_rule import CouponRewardRule, RewardTriggerType
from app.models.user_coupon import UserCoupon
from app.models.order import Order
from app.models.user import User
from app.schemas.coupon_reward import CouponRewardRuleCreate, CouponRewardRuleUpdate
from app.core.exceptions import NotFoundError, ValidationError
from app.services.email_service import EmailService
import logging

logger = logging.getLogger(__name__)


class CouponRewardService:
    """Service for managing coupon rewards and user coupons."""

    # ==================== Reward Rule Management ====================

    @staticmethod
    def create_rule(
        db: Session,
        rule_data: CouponRewardRuleCreate
    ) -> CouponRewardRule:
        """Create a new coupon reward rule."""
        rule = CouponRewardRule(
            name=rule_data.name,
            description=rule_data.description,
            trigger_type=rule_data.trigger_type.value,
            threshold_amount=float(rule_data.threshold_amount) if rule_data.threshold_amount else None,
            threshold_count=rule_data.threshold_count,
            coupon_discount_type=rule_data.coupon_discount_type.value,
            coupon_discount_value=float(rule_data.coupon_discount_value),
            coupon_minimum_order=float(rule_data.coupon_minimum_order) if rule_data.coupon_minimum_order else None,
            coupon_maximum_discount=float(rule_data.coupon_maximum_discount) if rule_data.coupon_maximum_discount else None,
            coupon_valid_days=rule_data.coupon_valid_days,
            is_active=rule_data.is_active,
            is_one_time=rule_data.is_one_time,
            priority=rule_data.priority
        )
        db.add(rule)
        db.commit()
        db.refresh(rule)
        return rule

    @staticmethod
    def get_rules(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None
    ) -> Tuple[List[CouponRewardRule], int]:
        """Get all coupon reward rules with pagination."""
        query = db.query(CouponRewardRule).order_by(CouponRewardRule.priority.desc())
        
        if is_active is not None:
            query = query.filter(CouponRewardRule.is_active == is_active)
        
        total_count = select(func.count()).select_from(query.subquery())
        total = db.execute(total_count).scalar()
        
        rules = query.offset(skip).limit(limit).all()
        return rules, total

    @staticmethod
    def get_rule_by_id(db: Session, rule_id: int) -> CouponRewardRule:
        """Get a specific rule by ID."""
        rule = db.query(CouponRewardRule).filter(CouponRewardRule.id == rule_id).first()
        if not rule:
            raise NotFoundError(detail="Coupon reward rule not found")
        return rule

    @staticmethod
    def update_rule(
        db: Session,
        rule_id: int,
        rule_update: CouponRewardRuleUpdate
    ) -> CouponRewardRule:
        """Update an existing rule."""
        rule = CouponRewardService.get_rule_by_id(db, rule_id)
        
        update_data = rule_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field in ['trigger_type', 'coupon_discount_type'] and value:
                setattr(rule, field, value.value)
            elif field in ['threshold_amount', 'coupon_minimum_order', 'coupon_maximum_discount', 'coupon_discount_value']:
                setattr(rule, field, float(value) if value else None)
            else:
                setattr(rule, field, value)
        
        db.commit()
        db.refresh(rule)
        return rule

    @staticmethod
    def delete_rule(db: Session, rule_id: int) -> None:
        """Delete a rule."""
        rule = CouponRewardService.get_rule_by_id(db, rule_id)
        db.delete(rule)
        db.commit()

    # ==================== Order Evaluation & Coupon Generation ====================

    @staticmethod
    def evaluate_order_and_generate_coupons(
        db: Session,
        order: Order,
        user: User
    ) -> List[UserCoupon]:
        """
        Evaluate an order against all active rules and generate coupons if conditions are met.
        Called after an order is successfully placed.
        """
        generated_coupons = []
        
        # Get all active rules, ordered by priority
        active_rules = db.query(CouponRewardRule).filter(
            CouponRewardRule.is_active == True
        ).order_by(CouponRewardRule.priority.desc()).all()
        
        for rule in active_rules:
            # Check if user already has a coupon from this one-time rule
            if rule.is_one_time:
                existing_coupon = db.query(UserCoupon).filter(
                    UserCoupon.user_id == user.id,
                    UserCoupon.reward_rule_id == rule.id
                ).first()
                if existing_coupon:
                    continue
            
            # Evaluate rule based on trigger type
            should_generate = False
            
            if rule.trigger_type == RewardTriggerType.ORDER_AMOUNT.value:
                # Check if order amount meets threshold
                if rule.threshold_amount and float(order.total_amount) >= float(rule.threshold_amount):
                    should_generate = True
                    
            elif rule.trigger_type == RewardTriggerType.ORDER_COUNT.value:
                # Count user's total orders (including this one)
                order_count = db.query(func.count(Order.id)).filter(
                    Order.user_id == user.id
                ).scalar() or 0
                
                if rule.threshold_count and order_count >= rule.threshold_count:
                    # Check if we already gave a coupon for reaching this milestone
                    if rule.is_one_time:
                        # One-time rules: only generate once
                        should_generate = True
                    else:
                        # Recurring rules: check if order count is exactly at milestone
                        # or is a multiple of threshold
                        if order_count == rule.threshold_count or order_count % rule.threshold_count == 0:
                            should_generate = True
            
            if should_generate:
                coupon = CouponRewardService._generate_coupon_for_user(
                    db=db,
                    user=user,
                    rule=rule,
                    triggered_by_order=order
                )
                generated_coupons.append(coupon)
        
        return generated_coupons

    @staticmethod
    def _generate_coupon_for_user(
        db: Session,
        user: User,
        rule: CouponRewardRule,
        triggered_by_order: Optional[Order] = None
    ) -> UserCoupon:
        """Generate a unique coupon code for a user based on a rule."""
        # Generate unique code
        code = UserCoupon.generate_coupon_code(prefix="REWARD")
        
        # Make sure code is unique
        while db.query(UserCoupon).filter(UserCoupon.code == code).first():
            code = UserCoupon.generate_coupon_code(prefix="REWARD")
        
        # Calculate validity period
        valid_from = datetime.now(timezone.utc)
        valid_until = valid_from + timedelta(days=rule.coupon_valid_days)
        
        coupon = UserCoupon(
            code=code,
            user_id=user.id,
            reward_rule_id=rule.id,
            triggered_by_order_id=triggered_by_order.id if triggered_by_order else None,
            discount_type=rule.coupon_discount_type,
            discount_value=rule.coupon_discount_value,
            minimum_order_amount=rule.coupon_minimum_order,
            maximum_discount_amount=rule.coupon_maximum_discount,
            valid_from=valid_from,
            valid_until=valid_until,
            is_used=False,
            email_sent=False
        )
        
        db.add(coupon)
        db.commit()
        db.refresh(coupon)
        
        logger.info(f"Generated coupon {code} for user {user.id} from rule {rule.id}")
        
        return coupon

    # ==================== Email Notification ====================

    @staticmethod
    def send_coupon_email(db: Session, coupon: UserCoupon) -> bool:
        """Send an email notification to the user about their new coupon."""
        try:
            user = coupon.user
            
            # Format discount text
            if coupon.discount_type == "percentage":
                discount_text = f"{coupon.discount_value}% off"
            else:
                discount_text = f"${coupon.discount_value} off"
            
            # Build email content
            subject = f"🎉 You've Earned a Coupon! {discount_text}"
            
            content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                    <h1 style="color: white; margin: 0;">🎁 Congratulations!</h1>
                    <p style="color: white; font-size: 18px;">You've earned a reward coupon!</p>
                </div>
                
                <div style="padding: 30px; background: #f9f9f9;">
                    <p>Hi <strong>{user.first_name}</strong>,</p>
                    
                    <p>Thank you for being a valued customer! As a reward for your purchase, here's a special coupon just for you:</p>
                    
                    <div style="background: white; border: 2px dashed #667eea; padding: 20px; text-align: center; margin: 20px 0; border-radius: 10px;">
                        <p style="font-size: 14px; color: #666; margin: 0;">Your Coupon Code</p>
                        <p style="font-size: 28px; font-weight: bold; color: #667eea; letter-spacing: 3px; margin: 10px 0;">
                            {coupon.code}
                        </p>
                        <p style="font-size: 24px; color: #333; margin: 10px 0;">{discount_text}</p>
                    </div>
                    
                    <div style="background: white; padding: 15px; border-radius: 8px; margin: 20px 0;">
                        <p style="font-size: 14px; color: #666; margin: 5px 0;">
                            ✅ Valid Until: <strong>{coupon.valid_until.strftime('%B %d, %Y')}</strong>
                        </p>
                        {f'<p style="font-size: 14px; color: #666; margin: 5px 0;">✅ Minimum Order: <strong>${coupon.minimum_order_amount}</strong></p>' if coupon.minimum_order_amount else ''}
                        {f'<p style="font-size: 14px; color: #666; margin: 5px 0;">✅ Maximum Discount: <strong>${coupon.maximum_discount_amount}</strong></p>' if coupon.maximum_discount_amount else ''}
                    </div>
                    
                    <p>Use this code at checkout to enjoy your savings!</p>
                    
                    <p style="color: #888; font-size: 12px;">
                        This coupon code is unique to your account and can only be used once.
                    </p>
                </div>
                
                <div style="background: #333; color: white; padding: 20px; text-align: center; border-radius: 0 0 10px 10px;">
                    <p style="margin: 0; font-size: 14px;">Thank you for shopping with us!</p>
                </div>
            </body>
            </html>
            """
            
            # Send email
            EmailService.send_email(
                db=db,
                recipient_email=user.email,
                subject=subject,
                template_name="coupon_reward",
                content=content
            )
            
            # Update coupon email status
            coupon.email_sent = True
            coupon.email_sent_at = datetime.now(timezone.utc)
            db.commit()
            
            logger.info(f"Coupon email sent to {user.email} for coupon {coupon.code}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send coupon email for coupon {coupon.id}: {str(e)}")
            return False

    # ==================== User Coupon Management ====================

    @staticmethod
    def get_user_coupons(
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 50,
        include_used: bool = False,
        include_expired: bool = False
    ) -> Tuple[List[UserCoupon], int]:
        """Get all coupons for a user."""
        query = db.query(UserCoupon).filter(UserCoupon.user_id == user_id)
        
        if not include_used:
            query = query.filter(UserCoupon.is_used == False)
        
        if not include_expired:
            query = query.filter(UserCoupon.valid_until >= datetime.now(timezone.utc))
        
        total = query.count()
        coupons = query.order_by(UserCoupon.created_at.desc()).offset(skip).limit(limit).all()
        
        return coupons, total

    @staticmethod
    def validate_coupon(
        db: Session,
        coupon_code: str,
        user_id: int,
        order_amount: float
    ) -> UserCoupon:
        """
        Validate a coupon code for checkout.
        Supports both personal coupons and public promo codes.
        Returns the coupon if valid, raises exception otherwise.
        """
        # Find the coupon
        coupon = db.query(UserCoupon).filter(UserCoupon.code == coupon_code).first()
        
        if not coupon:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Coupon code not found"
            )
        
        # For personal coupons, check ownership
        if not coupon.is_public and coupon.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This coupon code does not belong to your account"
            )
        
        # For personal coupons, check if already used
        if not coupon.is_public and coupon.is_used:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This coupon has already been used"
            )
        
        # For public coupons, check usage limit
        if coupon.is_public:
            if coupon.usage_limit and coupon.usage_count >= coupon.usage_limit:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This coupon has reached its usage limit"
                )
        
        # Check if expired
        if coupon.is_expired:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"This coupon expired on {coupon.valid_until.strftime('%B %d, %Y')}"
            )
        
        # Check minimum order amount
        if not coupon.can_apply_to_order(order_amount):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Order amount does not meet the minimum requirement of ${coupon.minimum_order_amount}"
            )
        
        return coupon

    @staticmethod
    def mark_coupon_as_used(
        db: Session,
        coupon: UserCoupon,
        order_id: int,
        user_id: int
    ) -> UserCoupon:
        """Mark a coupon as used after successful order."""
        if coupon.is_public:
            # For public coupons, increment usage count
            coupon.usage_count += 1
        else:
            # For personal coupons, mark as used
            coupon.is_used = True
            coupon.used_at = datetime.now(timezone.utc)
            coupon.used_on_order_id = order_id
        
        db.commit()
        db.refresh(coupon)
        return coupon

    # ==================== Public Coupon (Promo Code) Management ====================

    @staticmethod
    def create_public_coupon(
        db: Session,
        name: str,
        description: Optional[str],
        discount_type: str,
        discount_value: float,
        minimum_order_amount: Optional[float],
        maximum_discount_amount: Optional[float],
        valid_from: Optional[datetime],
        valid_until: datetime,
        usage_limit: Optional[int]
    ) -> UserCoupon:
        """Create a public promo code that any user can use."""
        # Auto-generate code if not provided
        code = UserCoupon.generate_coupon_code(prefix="PROMO", length=5)
        # Check if code already exists
        existing = db.query(UserCoupon).filter(UserCoupon.code == code).first()
        if existing:
            code = UserCoupon.generate_coupon_code(prefix="PROMO", length=5)
        
        now = datetime.now(timezone.utc)
        if valid_from and now < valid_from:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Coupon is not valid yet"
            )
        if valid_until and now > valid_until:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Coupon has expired"
            )

        coupon = UserCoupon(
            code=code,
            user_id=None,  # Public coupons don't belong to a specific user
            name=name,
            description=description,
            discount_type=discount_type,
            discount_value=discount_value,
            minimum_order_amount=minimum_order_amount,
            maximum_discount_amount=maximum_discount_amount,
            valid_from=valid_from.astimezone(timezone.utc),
            valid_until=valid_until.astimezone(timezone.utc),
            usage_limit=usage_limit,
            usage_count=0,
            is_public=True,
            is_used=False,
            email_sent=False
        )
        
        db.add(coupon)
        db.commit()
        db.refresh(coupon)
        
        logger.info(f"Created public coupon: {code}")
        return coupon

    @staticmethod
    def get_public_coupons(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        include_expired: bool = False
    ) -> Tuple[List[UserCoupon], int]:
        """Get all public coupons."""
        query = db.query(UserCoupon).filter(UserCoupon.is_public == True)
        
        if not include_expired:
            query = query.filter(UserCoupon.valid_until >= datetime.now(timezone.utc))
        
        total = query.count()
        coupons = query.order_by(UserCoupon.created_at.desc()).offset(skip).limit(limit).all()
        
        return coupons, total

    @staticmethod
    def update_public_coupon(
        db: Session,
        coupon_id: int,
        update_data: dict
    ) -> UserCoupon:
        """Update a public coupon."""
        coupon = db.query(UserCoupon).filter(
            UserCoupon.id == coupon_id,
            UserCoupon.is_public == True
        ).first()
        
        if not coupon:
            raise NotFoundError(detail="Public coupon not found")
        
        for field, value in update_data.items():
            if value is not None:
                if field == 'discount_type' and hasattr(value, 'value'):
                    setattr(coupon, field, value.value)
                else:
                    setattr(coupon, field, value)
        
        db.commit()
        db.refresh(coupon)
        return coupon

    @staticmethod
    def delete_public_coupon(db: Session, coupon_id: int) -> None:
        """Delete a public coupon."""
        coupon = db.query(UserCoupon).filter(
            UserCoupon.id == coupon_id,
            UserCoupon.is_public == True
        ).first()
        
        if not coupon:
            raise NotFoundError(detail="Public coupon not found")
        
        db.delete(coupon)
        db.commit()

