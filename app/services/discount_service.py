from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.discount import Discount
from app.schemas.discount import DiscountCreate, DiscountUpdate
from app.core.exceptions import NotFoundException

def create_discount(db: Session, discount: DiscountCreate) -> Discount:
    """
    Create a new discount.
    """
    db_discount = Discount(**discount.model_dump())
    db.add(db_discount)
    db.commit()
    db.refresh(db_discount)
    return db_discount

def get_discount(db: Session, discount_id: int) -> Optional[Discount]:
    """
    Get a single discount by ID.
    """
    return db.query(Discount).filter(Discount.id == discount_id).first()

def get_discount_by_name(db: Session, name: str) -> Optional[Discount]:
    """
    Get a single discount by its name (case-insensitive).
    """
    return db.query(Discount).filter(Discount.name == name).first()

def get_discounts(db: Session, skip: int = 0, limit: int = 100) -> List[Discount]:
    """
    Get a list of all discounts.
    """
    return db.query(Discount).offset(skip).limit(limit).all()

def update_discount(db: Session, discount_id: int, discount_update: DiscountUpdate) -> Optional[Discount]:
    """
    Update an existing discount.
    """
    db_discount = get_discount(db, discount_id)
    if not db_discount:
        return None
    
    update_data = discount_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_discount, key, value)
        
    db.commit()
    db.refresh(db_discount)
    return db_discount

def delete_discount(db: Session, discount_id: int) -> bool:
    """
    Delete a discount.
    """
    db_discount = get_discount(db, discount_id)
    if not db_discount:
        return False
    
    db.delete(db_discount)
    db.commit()
    return True

def validate_and_get_discount(db: Session, discount_name: str, order_amount: float) -> Discount:
    """
    Validates a discount and returns the Discount object if it's applicable.
    Raises exceptions for invalid conditions.
    """
    discount = get_discount_by_name(db, name=discount_name)

    if not discount:
        raise NotFoundException(f"Discount '{discount_name}' not found.")

    if not discount.is_valid:
        raise ValidationError("Discount is not valid, has expired, or reached its usage limit.")

    if not discount.can_apply_to_order(order_amount):
        raise ValidationError(
            f"Order amount does not meet the minimum requirement of ${discount.minimum_order_amount} for this discount."
        )

    return discount


def increment_discount_usage(db: Session, discount: Discount,- quantity: int = 1):
    """
    Increments the usage count of a discount.
    """
    discount.used_count += quantity
    db.commit()
    db.refresh(discount)
