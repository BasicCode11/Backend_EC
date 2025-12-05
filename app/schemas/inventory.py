from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal


class InventoryBase(BaseModel):
    variant_id: int
    stock_quantity: int = Field(0, ge=0)
    reserved_quantity: Optional[int] = Field(None, ge=0)
    low_stock_threshold: int = Field(10, ge=0)
    reorder_level: int = Field(5, ge=0)
    sku: Optional[str] = Field(None, max_length=100)
    batch_number: Optional[str] = Field(None, max_length=100)
    expiry_date: Optional[datetime] = None
    location: Optional[str] = Field(None, max_length=100)


class InventoryCreate(InventoryBase):
    pass


class InventoryUpdate(BaseModel):
    stock_quantity: Optional[int] = Field(None, ge=0)
    reserved_quantity: Optional[int] = Field(None, ge=0)
    low_stock_threshold: Optional[int] = Field(None, ge=0)
    reorder_level: Optional[int] = Field(None, ge=0)
    sku: Optional[str] = Field(None, max_length=100)
    batch_number: Optional[str] = Field(None, max_length=100)
    expiry_date: Optional[datetime] = None
    location: Optional[str] = Field(None, max_length=100)


class InventoryAdjustment(BaseModel):
    quantity: int
    reason: Optional[str] = Field(None, max_length=500)


class InventoryReserve(BaseModel):
    quantity: int = Field(..., ge=1)
    order_id: Optional[int] = None


class InventoryRelease(BaseModel):
    quantity: int = Field(..., ge=1)
    order_id: Optional[int] = None


class InventoryTransfer(BaseModel):
    from_inventory_id: int
    to_inventory_id: int
    quantity: int = Field(..., ge=1)
    reason: Optional[str] = Field(None, max_length=500)


class VariantSimple(BaseModel):
    id: int
    variant_name: str
    sku: Optional[str] = None
    additional_price: Decimal
    color: Optional[str] = None
    size: Optional[str] = None
    class Config:
        from_attributes = True


class InventoryResponse(InventoryBase):
    id: int
    available_quantity: int
    is_low_stock: bool
    needs_reorder: bool
    is_expired: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InventoryWithVariant(InventoryResponse):
    variant: Optional[VariantSimple] = None

    class Config:
        from_attributes = True


class InventoryListResponse(BaseModel):
    items: list[InventoryWithVariant]
    total: int
    page: int
    limit: int
    pages: int


class InventoryStatsResponse(BaseModel):
    total_products: int
    total_stock: int
    total_reserved: int
    total_available: int
    low_stock_count: int
    needs_reorder_count: int
    expired_count: int
    out_of_stock_count: int


class InventorySearchParams(BaseModel):
    search: Optional[str] = None
    variant_id: Optional[int] = None
    location: Optional[str] = None
    low_stock: Optional[bool] = None
    needs_reorder: Optional[bool] = None
    expired: Optional[bool] = None
    min_stock: Optional[int] = Field(None, ge=0)
    max_stock: Optional[int] = Field(None, ge=0)
    page: int = Field(1, ge=1)
    limit: int = Field(20, ge=1, le=100)
    sort_by: Optional[str] = Field(None, pattern="^(stock_quantity|available_quantity|created_at|updated_at)$")
    sort_order: Optional[str] = Field("asc", pattern="^(asc|desc)$")
