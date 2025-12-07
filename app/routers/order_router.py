from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from math import ceil

from app.database import get_db
from app.models.user import User
from app.schemas.order import (
    CheckoutRequest,
    OrderResponse,
    OrderWithDetails,
    OrderListResponse,
    OrderUpdate,
    OrderStatus as OrderStatusEnum,
    PaymentStatus as PaymentStatusEnum
)
from app.services.order_service import OrderService
from app.deps.auth import get_current_active_user, require_permission
from app.core.exceptions import ValidationError, NotFoundError

router = APIRouter()


@router.post("/checkout", response_model=OrderWithDetails, status_code=status.HTTP_201_CREATED)
def checkout(
    request: Request,
    checkout_data: CheckoutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    **Checkout and create order from cart.**
    
    This endpoint:
    1. ✅ Validates stock availability for all cart items
    2. ✅ Reserves inventory 
    3. ✅ Creates the order
    4. ✅ **Reduces stock quantities** from inventory
    5. ✅ Clears the cart
    
    **Stock Reduction:** When you place an order, the stock is automatically reduced:
    - `inventory.stock_quantity` is decreased
    - `inventory.reserved_quantity` is decreased
    - Both happen atomically in a transaction
    
    **Requirements:**
    - Cart must have items
    - All items must have sufficient stock
    - Valid shipping address required
    - Email must be verified
    
    **Returns:** Complete order details with all items
    """
    ip_address = request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or \
                 request.headers.get("X-Real-IP", "") or \
                 (request.client.host if request.client else None)
    user_agent = request.headers.get("User-Agent")
    
    try:
        order = OrderService.create_from_checkout(
            db=db,
            checkout_data=checkout_data,
            current_user=current_user,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Reload with items for response
        order = OrderService.get_by_id(db, order.id)
        
        # Build response manually to avoid duplicate 'items' parameter
        return OrderWithDetails(
            id=order.id,
            order_number=order.order_number,
            user_id=order.user_id,
            status=order.status,
            subtotal=order.subtotal,
            tax_amount=order.tax_amount,
            shipping_amount=order.shipping_amount,
            discount_amount=order.discount_amount,
            total_amount=order.total_amount,
            payment_status=order.payment_status,
            shipping_address_id=order.shipping_address_id,
            billing_address_id=order.billing_address_id,
            notes=order.notes,
            created_at=order.created_at,
            updated_at=order.updated_at,
            items=[item for item in order.items],
            total_items=order.total_items
        )
    
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create order: {str(e)}"
        )


@router.get("/orders", response_model=OrderListResponse)
def list_orders(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[OrderStatusEnum] = None,
    payment_status: Optional[PaymentStatusEnum] = None,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["orders:read"]))
):
    """
    **List all orders (Admin only).**
    
    Requires `orders:read` permission.
    
    Filters:
    - status: Filter by order status
    - payment_status: Filter by payment status
    - user_id: Filter by customer
    - page/limit: Pagination
    """
    skip = (page - 1) * limit
    status_value = status.value if status else None
    payment_value = payment_status.value if payment_status else None
    
    orders, total = OrderService.get_all(
        db=db,
        skip=skip,
        limit=limit,
        user_id=user_id,
        status=status_value,
        payment_status=payment_value
    )
    
    pages = ceil(total / limit) if total > 0 else 0
    
    return OrderListResponse(
        items=[OrderResponse.model_validate(o) for o in orders],
        total=total,
        page=page,
        limit=limit,
        pages=pages
    )


@router.get("/orders/me", response_model=OrderListResponse)
def get_my_orders(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    **Get current user's orders.**
    
    Returns all orders placed by the authenticated user.
    """
    skip = (page - 1) * limit
    
    orders, total = OrderService.get_user_orders(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )
    
    pages = ceil(total / limit) if total > 0 else 0
    
    return OrderListResponse(
        items=[OrderResponse.model_validate(o) for o in orders],
        total=total,
        page=page,
        limit=limit,
        pages=pages
    )


@router.get("/orders/{order_id}", response_model=OrderWithDetails)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
    
):
    """
    **Get order details by ID.**
    
    Users can only view their own orders.
    Admins with `orders:read` permission can view any order.
    """
    order = OrderService.get_by_id(db, order_id)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Check permission
    has_admin_permission = "orders:read" in current_user.permissions
    is_own_order = order.user_id == current_user.id
    
    if not (is_own_order or has_admin_permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own orders"
        )
    
    return OrderWithDetails(
        id=order.id,
        order_number=order.order_number,
        user_id=order.user_id,
        status=order.status,
        subtotal=order.subtotal,
        tax_amount=order.tax_amount,
        shipping_amount=order.shipping_amount,
        discount_amount=order.discount_amount,
        total_amount=order.total_amount,
        payment_status=order.payment_status,
        shipping_address_id=order.shipping_address_id,
        billing_address_id=order.billing_address_id,
        notes=order.notes,
        created_at=order.created_at,
        updated_at=order.updated_at,
        items=[item for item in order.items],
        total_items=order.total_items
    )


@router.put("/orders/{order_id}", response_model=OrderResponse)
def update_order(
    request: Request,
    order_id: int,
    order_data: OrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["orders:update"]))
):
    """
    **Update order (Admin only).**
    
    Requires `orders:update` permission.
    
    Can update:
    - status
    - payment_status
    - shipping_address_id
    - billing_address_id
    - notes
    """
    ip_address = request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or \
                 request.headers.get("X-Real-IP", "") or \
                 (request.client.host if request.client else None)
    user_agent = request.headers.get("User-Agent")
    
    try:
        order = OrderService.update(
            db=db,
            order_id=order_id,
            order_data=order_data,
            current_user=current_user,
            ip_address=ip_address,
            user_agent=user_agent
        )
        return OrderResponse.model_validate(order)
    
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/orders/{order_id}/cancel", response_model=OrderResponse)
def cancel_order(
    request: Request,
    order_id: int,
    reason: Optional[str] = Query(None, max_length=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    **Cancel an order and restore inventory.**
    
    This endpoint:
    1. ✅ Validates order can be cancelled (only PENDING/PROCESSING)
    2. ✅ **Restores stock** to inventory
    3. ✅ Updates order status to CANCELLED
    
    **Stock Restoration:** When you cancel an order:
    - Stock quantities are added back to inventory
    - Audit logs track the restoration
    
    **Permission:**
    - Users can cancel their own orders
    - Admins can cancel any order
    """
    order = OrderService.get_by_id(db, order_id)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Check permission
    has_admin_permission = "orders:update" in current_user.permissions
    is_own_order = order.user_id == current_user.id
    
    if not (is_own_order or has_admin_permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only cancel your own orders"
        )
    
    ip_address = request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or \
                 request.headers.get("X-Real-IP", "") or \
                 (request.client.host if request.client else None)
    user_agent = request.headers.get("User-Agent")
    
    try:
        order = OrderService.cancel_order(
            db=db,
            order_id=order_id,
            current_user=current_user,
            reason=reason,
            ip_address=ip_address,
            user_agent=user_agent
        )
        return OrderResponse.model_validate(order)
    
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/orders/statistics", response_model=dict)
def get_order_statistics(
    user_id: Optional[int] = Query(None, description="Filter by user (admin only)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    **Get order statistics.**
    
    Users see their own stats.
    Admins can see all stats or filter by user.
    """
    # If user_id specified, check admin permission
    if user_id and user_id != current_user.id:
        if "orders:read" not in current_user.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin permission required to view other users' statistics"
            )
    elif not user_id:
        # Regular users see their own stats only
        if "orders:read" not in current_user.permissions:
            user_id = current_user.id
    
    stats = OrderService.get_statistics(db, user_id=user_id)
    return stats
