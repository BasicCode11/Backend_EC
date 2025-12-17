from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.discount import DiscountCreate, DiscountUpdate, DiscountResponse
from app.services import discount_service
from app.deps.permission import check_permissions
from app.models.user import User

router = APIRouter()

@router.post(
    "/", 
    response_model=DiscountResponse, 
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(check_permissions(["discount:create"]))],
    summary="Create a new discount",
    tags=["Discounts"]
)
def create_discount(
    discount: DiscountCreate, 
    db: Session = Depends(get_db)
):
    """
    Create a new discount with the specified details.
    
    Permissions:
    - Requires `discount:create`
    """
    return discount_service.create_discount(db=db, discount=discount)

@router.get(
    "/", 
    response_model=List[DiscountResponse],
    dependencies=[Depends(check_permissions(["discount:read"]))],
    summary="Get all discounts",
    tags=["Discounts"]
)
def read_discounts(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """
    Retrieve a list of all discounts.
    
    Permissions:
    - Requires `discount:read`
    """
    discounts = discount_service.get_discounts(db, skip=skip, limit=limit)
    return discounts

@router.get(
    "/{discount_id}", 
    response_model=DiscountResponse,
    dependencies=[Depends(check_permissions(["discount:read"]))],
    summary="Get a specific discount",
    tags=["Discounts"]
)
def read_discount(
    discount_id: int, 
    db: Session = Depends(get_db)
):
    """
    Retrieve a specific discount by its ID.
    
    Permissions:
    - Requires `discount:read`
    """
    db_discount = discount_service.get_discount(db, discount_id=discount_id)
    if db_discount is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Discount not found")
    return db_discount

@router.put(
    "/{discount_id}", 
    response_model=DiscountResponse,
    dependencies=[Depends(check_permissions(["discount:update"]))],
    summary="Update a discount",
    tags=["Discounts"]
)
def update_discount(
    discount_id: int, 
    discount: DiscountUpdate, 
    db: Session = Depends(get_db)
):
    """
    Update an existing discount's details.
    
    Permissions:
    - Requires `discount:update`
    """
    db_discount = discount_service.update_discount(db, discount_id=discount_id, discount_update=discount)
    if db_discount is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Discount not found")
    return db_discount

@router.delete(
    "/{discount_id}", 
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(check_permissions(["discount:delete"]))],
    summary="Delete a discount",
    tags=["Discounts"]
)
def delete_discount(
    discount_id: int, 
    db: Session = Depends(get_db)
):
    """
    Delete a discount from the system.
    
    Permissions:
    - Requires `discount:delete`
    """
    success = discount_service.delete_discount(db, discount_id=discount_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Discount not found")
    return {"ok": True}
