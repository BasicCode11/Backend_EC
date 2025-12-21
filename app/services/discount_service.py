from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException , status
from sqlalchemy import select , func
from app.models.discount import Discount
from app.schemas.discount import DiscountCreate, DiscountUpdate
from app.core.exceptions import NotFoundError, ValidationError
from app.models.user import User
from app.services.audit_log_service import AuditLogService
class DiscountService:

    @staticmethod
    def get_discounts(
        db: Session, 
        skip: int = 0, 
        limit: int = 100, 
        is_active: Optional[bool] = None,
        search: Optional[str] = None
    ) -> tuple[List[Discount], int]:
        """Retrieve a list of discounts with optional filtering by active status and name search"""
        query = db.query(Discount).order_by(Discount.created_at.desc())
        if is_active is not None:
            query = query.filter(Discount.is_active == is_active)
        if search:
            query = query.filter(Discount.name.ilike(f"%{search}%"))
        total_count = select(func.count()).select_from(query.subquery())
        total = db.execute(total_count).scalar()
        
        discounts = query.offset(skip).limit(limit).all()
        return discounts , total
    
    @staticmethod
    def get_discount_byid(db: Session, discount_id: int) -> Discount:
        """Retrieve a discount by its ID"""
        discount = db.query(Discount).filter(Discount.id == discount_id).first()
        if not discount:
            raise NotFoundError(detail="Discount not found")
        return discount

    @staticmethod
    def create_discount(db: Session, discount: DiscountCreate, created_by: User , ip_address: str, user_agent: str) -> Discount:
        """Create a new discount"""
        db_discount = Discount(
            name=discount.name,
            description=discount.description,
            discount_type=discount.discount_type.value,
            discount_value=float(discount.discount_value),
            minimum_order_amount=float(discount.minimum_order_amount) if discount.minimum_order_amount else None,
            maximum_discount_amount=float(discount.maximum_discount_amount) if discount.maximum_discount_amount else None,
            usage_limit=discount.usage_limit,
            valid_from=discount.valid_from,
            valid_until=discount.valid_until,
            is_active=discount.is_active,
            apply_to=discount.apply_to.value
        )
        db.add(db_discount)
        db.commit()
        db.refresh(db_discount)
        
        # Log the creation action
        AuditLogService.log_create(
            db=db,
            user_id=created_by.id,
            entity_type="Discount",
            entity_id=db_discount.id,
            ip_address=ip_address,
            user_agent=user_agent,
            new_values={
                "name": db_discount.name,
                "description": db_discount.description,
                "discount_type": db_discount.discount_type,
                "discount_value": float(db_discount.discount_value),
                "minimum_order_amount": float(db_discount.minimum_order_amount) if db_discount.minimum_order_amount else None,
                "maximum_discount_amount": float(db_discount.maximum_discount_amount) if db_discount.maximum_discount_amount else None,
                "usage_limit": db_discount.usage_limit,
                "is_active": db_discount.is_active,
                "apply_to": db_discount.apply_to
            }
        )

        return db_discount
    
    @staticmethod
    def update_discount(db: Session, discount_id: int, discount_update: DiscountUpdate)-> Discount:
        """Update an existing discount"""
        discount = db.query(Discount).filter(Discount.id == discount_id).first()
        if not discount:
            raise NotFoundError(detail="Discount not found")
        
        
        for field, value in discount_update.dict(exclude_unset=True).items():
            setattr(discount, field, value)
        
        db.commit()
        db.refresh(discount)
        AuditLogService.log_update(
            db=db,
            user_id=None,  # You can pass the user ID if available
            entity_type="Discount",
            entity_id=discount.id,
            old_values={
                "name": discount.name,
                "description": discount.description,
                "discount_type": discount.discount_type,
                "discount_value": float(discount.discount_value),
                "minimum_order_amount": float(discount.minimum_order_amount) if discount.minimum_order_amount else None,
                "maximum_discount_amount": float(discount.maximum_discount_amount) if discount.maximum_discount_amount else None,
                "usage_limit": discount.usage_limit if discount.usage_limit else None,
                "valid_from": str(discount.valid_from),
                "valid_until": str(discount.valid_until),
                "is_active": discount.is_active,
                "apply_to": discount.apply_to
            },
            new_values={
                "name": discount_update.name,
                "description": discount_update.description,
                "discount_type": discount_update.discount_type,
                "discount_value": float(discount_update.discount_value),
                "minimum_order_amount": float(discount_update.minimum_order_amount) if discount_update.minimum_order_amount else None,
                "maximum_discount_amount": float(discount_update.maximum_discount_amount) if discount_update.maximum_discount_amount else None,
                "usage_limit": discount_update.usage_limit if discount_update.usage_limit else None,
                "valid_from": str(discount_update.valid_from),
                "valid_until": str(discount_update.valid_until),
                "is_active": discount_update.is_active,
                "apply_to": discount_update.apply_to
            }
        )

        return discount
    

    @staticmethod
    def delete_discount(db: Session, discount_id: int, deleted_by: User) -> None:
        """Delete a discount by its ID"""
        discount = db.query(Discount).filter(Discount.id == discount_id).first()
        if not discount:
            raise NotFoundError(detail="Discount not found")
        
        db.delete(discount)
        db.commit()

        # Log the deletion action
        AuditLogService.log_delete(
            db=db,
            user_id=deleted_by.id,
            entity_type="Discount",
            entity_id=discount.id,
            old_values={
                "name": discount.name,
                "description": discount.description,
                "discount_type": discount.discount_type,
                "discount_value": float(discount.discount_value),
                "minimum_order_amount": float(discount.minimum_order_amount) if discount.minimum_order_amount else None,
                "maximum_discount_amount": float(discount.maximum_discount_amount) if discount.maximum_discount_amount else None,
                "usage_limit": discount.usage_limit if discount.usage_limit else None,
                "valid_from": str(discount.valid_from),
                "valid_until": str(discount.valid_until),
                "is_active": discount.is_active,
                "apply_to": discount.apply_to
            }
        )

        return {"message": "Discount deleted successfully"}

    @staticmethod
    def get_discount_by_name(db: Session, discount_name: str) -> Discount:
        return db.query(Discount).filter(Discount.name == discount_name).first()

    @staticmethod
    def validate_and_get_discount(db: Session, discount_name: str, order_amount: float) -> Discount:
        discount = DiscountService.get_discount_by_name(db, discount_name)
        if not discount:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Discount not found")
        
        if not discount.is_valid:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Discount is not valid, has expired, or reached its usage limit.")
        
        if not discount.can_apply_to_order(order_amount):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Order amount does not meet the minimum requirement of ${discount.minimum_order_amount} for this discount."
            )
        
        return discount

    @staticmethod
    def increment_discount_usage(db: Session, discount: Discount, quantity: int = 1):
        discount.used_count += quantity
        db.commit()
        db.refresh(discount)