from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.wishlist import (
    WishlistItemAdd,
    WishlistItemResponse,
    WishlistResponse,
    WishlistCountResponse
)
from app.services.wishlist_service import WishlistService
from app.deps.auth import get_current_active_user
from app.core.exceptions import ValidationError, NotFoundError

router = APIRouter()


@router.get("/wishlist", response_model=WishlistResponse)
def get_wishlist(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    **Get user's wishlist**
    
    Returns all items in the wishlist with:
    - Product details
    - Variant information (if applicable)
    - Current stock status
    - Product images
    - Prices
    
    Items ordered by most recently added.
    """
    wishlist_items = WishlistService.get_user_wishlist(db, current_user.id)
    
    items = []
    for item in wishlist_items:
        product = item.product
        variant = item.variant
        
        # Get product image
        image_url = None
        if product.images and len(product.images) > 0:
            image_url = product.images[0].image_url
        
        # Get stock
        stock = WishlistService.get_product_stock(db, product.id)
        
        # Determine price
        price = variant.effective_price if variant else product.price
        
        items.append(WishlistItemResponse(
            id=item.id,
            user_id=item.user_id,
            product_id=item.product_id,
            variant_id=item.variant_id,
            product_name=product.name,
            product_price=product.price,
            variant_name=variant.name if variant else None,
            variant_price=variant.effective_price if variant else None,
            image_url=image_url,
            is_available=stock > 0,
            stock_quantity=stock,
            created_at=item.created_at
        ))
    
    return WishlistResponse(
        items=items,
        total_items=len(items)
    )


@router.post("/wishlist", response_model=WishlistItemResponse, status_code=status.HTTP_201_CREATED)
def add_to_wishlist(
    wishlist_data: WishlistItemAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    **Add item to wishlist**
    
    Add a product (and optional variant) to your wishlist.
    
    **Parameters:**
    - product_id: Required
    - variant_id: Optional (for products with variants)
    
    **Features:**
    - Prevents duplicate items
    - Validates product and variant exist
    - Instant add (no cart required)
    
    **Use Cases:**
    - Save items for later
    - Create shopping lists
    - Track desired products
    - Share wishlist with others
    """
    try:
        wishlist_item = WishlistService.add_to_wishlist(
            db=db,
            user_id=current_user.id,
            wishlist_data=wishlist_data
        )
        
        # Get product details
        product = wishlist_item.product
        variant = wishlist_item.variant
        
        image_url = None
        if product.images and len(product.images) > 0:
            image_url = product.images[0].image_url
        
        stock = WishlistService.get_product_stock(db, product.id)
        price = variant.effective_price if variant else product.price
        
        return WishlistItemResponse(
            id=wishlist_item.id,
            user_id=wishlist_item.user_id,
            product_id=wishlist_item.product_id,
            variant_id=wishlist_item.variant_id,
            product_name=product.name,
            product_price=product.price,
            variant_name=variant.variant_name if variant else None,
            variant_price=variant.effective_price if variant else None,
            image_url=image_url,
            is_available=stock > 0,
            stock_quantity=stock,
            created_at=wishlist_item.created_at
        )
    
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/wishlist/{wishlist_item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_wishlist(
    wishlist_item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    **Remove item from wishlist**
    
    Remove a specific item from your wishlist by wishlist item ID.
    """
    try:
        WishlistService.remove_from_wishlist(
            db=db,
            user_id=current_user.id,
            wishlist_item_id=wishlist_item_id
        )
        return {"message": "Removed favorite successfully."}
    
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/wishlist/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_product_from_wishlist(
    product_id: int,
    variant_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    **Remove product from wishlist**
    
    Remove a product from wishlist by product_id (and optional variant_id).
    Useful when you know the product ID but not the wishlist item ID.
    """
    try:
        WishlistService.remove_product_from_wishlist(
            db=db,
            user_id=current_user.id,
            product_id=product_id,
            variant_id=variant_id
        )
        return None
    
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/wishlist", status_code=status.HTTP_204_NO_CONTENT)
def clear_wishlist(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    **Clear entire wishlist**
    
    Remove all items from your wishlist at once.
    """
    WishlistService.clear_wishlist(db, current_user.id)
    return None


@router.get("/wishlist/count", response_model=WishlistCountResponse)
def get_wishlist_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    **Get wishlist item count**
    
    Returns the number of items in wishlist.
    Useful for displaying wishlist badge/counter in UI.
    """
    count = WishlistService.get_wishlist_count(db, current_user.id)
    return WishlistCountResponse(count=count)


@router.get("/wishlist/check/{product_id}")
def check_in_wishlist(
    product_id: int,
    variant_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    **Check if product is in wishlist**
    
    Returns whether the specified product (and variant) is in user's wishlist.
    Useful for showing/hiding "Add to Wishlist" button.
    """
    is_in_wishlist = WishlistService.is_in_wishlist(
        db=db,
        user_id=current_user.id,
        product_id=product_id,
        variant_id=variant_id
    )
    
    return {
        "product_id": product_id,
        "variant_id": variant_id,
        "in_wishlist": is_in_wishlist
    }


@router.post("/wishlist/{wishlist_item_id}/move-to-cart")
def move_wishlist_item_to_cart(
    wishlist_item_id: int,
    quantity: int = 1,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    **Move wishlist item to cart**
    
    Add item from wishlist to cart and remove it from wishlist.
    Convenience function for quick checkout from wishlist.
    
    **Parameters:**
    - wishlist_item_id: The wishlist item to move
    - quantity: Quantity to add to cart (default: 1)
    
    **Returns:**
    - Success message with cart details
    """
    try:
        # Get wishlist item
        from app.models.wishlist import Wishlist
        from app.services.cart_service import CartService
        from app.schemas.cart import AddToCartRequest
        
        wishlist_item = db.query(Wishlist).filter(
            Wishlist.id == wishlist_item_id,
            Wishlist.user_id == current_user.id
        ).first()
        
        if not wishlist_item:
            raise NotFoundError("Wishlist item not found")
        
        # Add to cart
        cart_data = AddToCartRequest(
            product_id=wishlist_item.product_id,
            variant_id=wishlist_item.variant_id,
            quantity=quantity
        )
        
        CartService.add_to_cart(
            db=db,
            user=current_user,
            cart_data=cart_data
        )
        
        # Remove from wishlist
        db.delete(wishlist_item)
        db.commit()
        
        return {
            "message": "Item moved to cart successfully",
            "product_id": wishlist_item.product_id,
            "variant_id": wishlist_item.variant_id,
            "quantity": quantity
        }
    
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
