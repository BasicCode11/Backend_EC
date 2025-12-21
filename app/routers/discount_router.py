from typing import Optional
from fastapi import APIRouter, Depends, Request, status , Query
from sqlalchemy.orm import Session
    
from app.database import get_db
from app.schemas.discount import DiscountCreate, DiscountUpdate, DiscountResponse , DiscountListResponse
from app.services.discount_service import DiscountService
from app.deps.auth import require_permission
from app.models.user import User
router = APIRouter()

@router.post("/discounts", response_model=DiscountResponse, status_code=status.HTTP_201_CREATED)
def create_discount(
    request: Request,
    discount: DiscountCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["discounts:create"]))
):
    """
    Create a new discount with the specified details.
    
    Permissions:
    - Requires `discount:create`
    """
    ip_address = request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or request.headers.get("X-Real-IP", "") or (request.client.host if request.client else None)
    user_agent = request.headers.get("User-Agent")
    return DiscountService.create_discount(db=db, discount=discount , created_by=current_user , ip_address=ip_address , user_agent=user_agent)

@router.get("/discounts", response_model=DiscountListResponse,dependencies=[Depends(require_permission(["discounts:read"]))],)
def read_discounts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    status: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by discount name"),
    db: Session = Depends(get_db)
):

    discounts , total = DiscountService.get_discounts(db, skip=skip, limit=limit , is_active=status, search=search)
    return {
        "discounts": discounts,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@router.get("/discounts/{discount_id}", response_model=DiscountResponse,dependencies=[Depends(require_permission(["discounts:read"]))])
def read_discount(
    discount_id: int, 
    db: Session = Depends(get_db)
):
    return DiscountService.get_discount_byid(db, discount_id=discount_id)

@router.put("/discounts/{discount_id}", response_model=DiscountResponse)
def update_discount(
    discount_id: int, 
    discount: DiscountUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["discounts:update"]))
):
    """
    Update an existing discount's details.
    
    Permissions:
    - Requires `discount:update`
    """
    return DiscountService.update_discount(db, discount_id=discount_id, discount_update=discount)
   

@router.delete("/discounts/{discount_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_discount(
    discount_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["discounts:delete"]))
):
   return DiscountService.delete_discount(db, discount_id=discount_id, deleted_by=current_user)
