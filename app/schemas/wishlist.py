from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


class WishlistItemAdd(BaseModel):
    """Request to add item to wishlist"""
    product_id: int
    variant_id: Optional[int] = None


class WishlistItemResponse(BaseModel):
    """Wishlist item with product details"""
    id: int
    user_id: int
    product_id: int
    variant_id: Optional[int] = None
    product_name: str
    product_price: Decimal
    variant_name: Optional[str] = None
    variant_price: Optional[Decimal] = None
    image_url: Optional[str] = None
    is_available: bool = True
    stock_quantity: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class WishlistResponse(BaseModel):
    """User's complete wishlist"""
    items: List[WishlistItemResponse]
    total_items: int


class WishlistCountResponse(BaseModel):
    """Wishlist item count"""
    count: int
