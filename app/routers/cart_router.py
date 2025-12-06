from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session
from typing import Optional
import uuid

from app.database import get_db
from app.models.user import User
from app.schemas.cart import (
    AddToCartRequest,
    UpdateCartItemRequest,
    ShoppingCartResponse,
    CartItemResponse
)
from app.services.cart_service import CartService
from app.deps.auth import get_current_user
from app.core.exceptions import ValidationError, NotFoundError

router = APIRouter()


def get_or_create_session_id(request: Request, response: Response) -> str:
    """Get session ID from cookie or create new one"""
    session_id = request.cookies.get("session_id")
    if not session_id:
        session_id = str(uuid.uuid4())
        response.set_cookie(
            key="session_id",
            value=session_id,
            max_age=30 * 24 * 60 * 60,  # 30 days
            httponly=True,
            samesite="lax"
        )
    return session_id


def transform_cart_response(cart) -> ShoppingCartResponse:
    """Transform cart ORM model to response schema"""
    items = []
    for item in cart.items:
        # Get stock info
        stock_available = 0
        if item.variant and item.variant.inventory:
            stock_available = sum(inv.available_quantity for inv in item.variant.inventory)
        
        # Get image
        if item.product and item.product.images:
            for img in item.product.images:
                if img.is_primary:
                    image_url = img.image_url
                    break
            if not image_url and item.product.images:
                image_url = item.product.images[0].image_url
        
        items.append(CartItemResponse(
            id=item.id,
            cart_id=item.cart_id,
            product_id=item.product_id,
            variant_id=item.variant_id,
            product_name=item.product.name,
            variant_name=item.variant.variant_name if item.variant else None,
            quantity=item.quantity,
            price=item.price,
            total_price=item.total_price,
            image_url=image_url,
            stock_available=stock_available,
            created_at=item.created_at,
            updated_at=item.updated_at
        ))
    
    return ShoppingCartResponse(
        id=cart.id,
        user_id=cart.user_id,
        session_id=cart.session_id,
        items=items,
        total_items=cart.total_items,
        total_amount=cart.total_amount,
        created_at=cart.created_at,
        updated_at=cart.updated_at
    )


@router.get("/cart", response_model=ShoppingCartResponse)
def get_cart(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    **Get shopping cart**
    
    - For authenticated users: Returns user's cart
    - For guests: Returns session cart (creates session cookie if needed)
    
    Cart includes:
    - All items with product details
    - Current stock availability
    - Product images
    - Total amounts
    """
    session_id = None if current_user else get_or_create_session_id(request, response)
    cart = CartService.get_cart(db, current_user, session_id)
    return transform_cart_response(cart)


@router.post("/cart/items", response_model=ShoppingCartResponse, status_code=status.HTTP_201_CREATED)
def add_to_cart(
    request: Request,
    response: Response,
    cart_data: AddToCartRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    **Add item to cart**
    
    - Validates product and variant exist
    - Checks stock availability
    - If item already in cart, increases quantity
    - Works for both guests and authenticated users
    
    **Stock Check:** Ensures sufficient inventory before adding
    """
    session_id = None if current_user else get_or_create_session_id(request, response)
    
    try:
        cart = CartService.add_to_cart(db, current_user, cart_data, session_id)
        return transform_cart_response(cart)
    except (ValidationError, NotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/cart/items/{cart_item_id}", response_model=ShoppingCartResponse)
def update_cart_item(
    request: Request,
    response: Response,
    cart_item_id: int,
    update_data: UpdateCartItemRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    **Update cart item quantity**
    
    - Changes quantity of existing cart item
    - Validates stock availability
    - Cannot set quantity below 1 (use DELETE instead)
    """
    session_id = None if current_user else get_or_create_session_id(request, response)
    
    try:
        cart = CartService.update_cart_item(db, current_user, cart_item_id, update_data, session_id)
        return transform_cart_response(cart)
    except (ValidationError, NotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/cart/items/{cart_item_id}", response_model=ShoppingCartResponse)
def remove_from_cart(
    request: Request,
    response: Response,
    cart_item_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    **Remove item from cart**
    
    Completely removes the item from cart.
    """
    session_id = None if current_user else get_or_create_session_id(request, response)
    
    try:
        cart = CartService.remove_from_cart(db, current_user, cart_item_id, session_id)
        return transform_cart_response(cart)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/cart", response_model=ShoppingCartResponse)
def clear_cart(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    **Clear entire cart**
    
    Removes all items from cart at once.
    """
    session_id = None if current_user else get_or_create_session_id(request, response)
    cart = CartService.clear_cart(db, current_user, session_id)
    return transform_cart_response(cart)


@router.post("/cart/merge", response_model=ShoppingCartResponse)
def merge_guest_cart(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    **Merge guest cart with user cart after login**
    
    Called automatically after login to merge:
    - Guest cart (from session) into
    - User cart (persistent)
    
    Duplicates are combined (quantities added).
    """
    session_id = request.cookies.get("session_id")
    if not session_id:
        # No guest cart to merge
        cart = CartService.get_cart(db, current_user, None)
        return transform_cart_response(cart)
    
    cart = CartService.merge_carts(db, current_user, session_id)
    return transform_cart_response(cart)
