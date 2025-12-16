from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from enum import Enum


class OrderStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"


# Order Item Schemas
class OrderItemBase(BaseModel):
    product_id: int
    variant_id: Optional[int] = None
    quantity: int = Field(..., ge=1)
    unit_price: Decimal


class OrderItemCreate(OrderItemBase):
    pass


class OrderItemResponse(BaseModel):
    id: int
    order_id: int
    product_id: int
    variant_id: Optional[int] = None
    product_name: str
    product_sku: Optional[str] = None
    variant_attributes: Optional[dict] = None
    quantity: int
    unit_price: Decimal
    total_price: Decimal
    created_at: datetime

    class Config:
        from_attributes = True


# Order Schemas
class OrderBase(BaseModel):
    shipping_address_id: Optional[int] = None
    billing_address_id: Optional[int] = None
    notes: Optional[str] = None


class CheckoutRequest(BaseModel):
    """
    Request to create an order from cart items.
    Optionally provide specific items, otherwise uses all cart items.
    """
    shipping_address_id: int = Field(..., description="Shipping address ID")
    billing_address_id: Optional[int] = Field(None, description="Billing address ID (defaults to shipping)")
    notes: Optional[str] = Field(None, max_length=500)
    payment_method: Optional[str] = Field(None, description="Payment method (for future use)")


class OrderCreate(OrderBase):
    """Internal schema for creating orders"""
    items: List[OrderItemCreate]


class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None
    shipping_address_id: Optional[int] = None
    billing_address_id: Optional[int] = None
    notes: Optional[str] = None

class UserOut(BaseModel):
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    id: int
    order_number: str
    user_id: int
    user: UserOut
    status: str
    subtotal: Decimal
    tax_amount: Decimal
    shipping_amount: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    payment_status: str
    shipping_address_id: Optional[int] = None
    billing_address_id: Optional[int] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrderWithDetails(OrderResponse):
    """Order with items included"""
    items: List[OrderItemResponse] = []
    total_items: int = 0

    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    items: List[OrderResponse]
    total: int
    page: int
    limit: int
    pages: int

class DashboardOrderResponse(BaseModel):
    items: List[OrderResponse]
    total: int
    
class OrderSearchParams(BaseModel):
    status: Optional[OrderStatus] = None
    payment_status: Optional[PaymentStatus] = None
    user_id: Optional[int] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    page: int = Field(1, ge=1)
    limit: int = Field(20, ge=1, le=100)
    sort_by: Optional[str] = Field(None, pattern="^(created_at|updated_at|total_amount|order_number)$")
    sort_order: Optional[str] = Field("desc", pattern="^(asc|desc)$")
