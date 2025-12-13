from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


# Cart Item Schemas
class CartItemBase(BaseModel):
    product_id: int
    variant_id: Optional[int] = None
    quantity: int = Field(..., ge=1, description="Quantity must be at least 1")


class CartItemCreate(CartItemBase):
    pass


class CartItemUpdate(BaseModel):
    quantity: int = Field(..., ge=1, description="Quantity must be at least 1")


class CartItemResponse(BaseModel):
    id: int
    cart_id: int
    product_id: int
    variant_id: Optional[int] = None
    product_name: str
    variant_name: Optional[str] = None
    color: Optional[str] = None
    size: Optional[str] = None
    quantity: int
    price: Decimal
    total_price: Decimal
    image_url: Optional[str] = None
    stock_available: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Shopping Cart Schemas
class ShoppingCartResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    session_id: Optional[str] = None
    items: List[CartItemResponse] = []
    total_items: int = 0
    total_amount: Decimal = Decimal("0.00")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AddToCartRequest(BaseModel):
    product_id: int
    variant_id: Optional[int] = None
    quantity: int = Field(1, ge=1, description="Quantity to add")


class UpdateCartItemRequest(BaseModel):
    quantity: int = Field(..., ge=1, description="New quantity")


class ApplyDiscountRequest(BaseModel):
    discount_code: str = Field(..., min_length=1, max_length=50)
