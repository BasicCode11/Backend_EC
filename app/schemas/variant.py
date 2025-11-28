from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


# Inventory schemas for variants
class VariantInventoryCreate(BaseModel):
    """Schema for creating inventory when creating a variant"""
    stock_quantity: int = Field(0, ge=0)
    reserved_quantity: int = Field(0, ge=0)
    low_stock_threshold: int = Field(10, ge=0)
    reorder_level: int = Field(5, ge=0)
    sku: Optional[str] = Field(None, max_length=100)
    batch_number: Optional[str] = Field(None, max_length=100)
    expiry_date: Optional[datetime] = None
    location: Optional[str] = Field(None, max_length=100)


class VariantInventoryUpdate(BaseModel):
    """Schema for updating inventory when updating a variant"""
    stock_quantity: Optional[int] = Field(None, ge=0)
    reserved_quantity: Optional[int] = Field(None, ge=0)
    low_stock_threshold: Optional[int] = Field(None, ge=0)
    reorder_level: Optional[int] = Field(None, ge=0)
    sku: Optional[str] = Field(None, max_length=100)
    batch_number: Optional[str] = Field(None, max_length=100)
    expiry_date: Optional[datetime] = None
    location: Optional[str] = Field(None, max_length=100)


class VariantInventoryResponse(BaseModel):
    """Schema for inventory in variant responses"""
    id: int
    stock_quantity: int
    reserved_quantity: int
    available_quantity: int
    low_stock_threshold: int
    reorder_level: int
    is_low_stock: bool
    needs_reorder: bool
    sku: Optional[str] = None
    batch_number: Optional[str] = None
    expiry_date: Optional[datetime] = None
    location: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Variant schemas
class VariantBase(BaseModel):
    """Base schema for product variants"""
    sku: Optional[str] = Field(None, max_length=100)
    variant_name: str = Field(..., max_length=255)
    color: Optional[str] = Field(None, max_length=50)
    size: Optional[str] = Field(None, max_length=50)
    weight: Optional[str] = Field(None, max_length=20)
    additional_price: Optional[Decimal] = Field(None, ge=0)
    sort_order: int = Field(0, ge=0)


class VariantCreateWithInventory(VariantBase):
    """Schema for creating a variant with inventory"""
    inventory: List[VariantInventoryCreate] = Field(default_factory=list, description="List of inventory records for this variant")


class VariantUpdateWithInventory(BaseModel):
    """Schema for updating a variant with inventory"""
    sku: Optional[str] = Field(None, max_length=100)
    variant_name: Optional[str] = Field(None, max_length=255)
    color: Optional[str] = Field(None, max_length=50)
    size: Optional[str] = Field(None, max_length=50)
    weight: Optional[str] = Field(None, max_length=20)
    additional_price: Optional[Decimal] = Field(None, ge=0)
    sort_order: Optional[int] = Field(None, ge=0)
    inventory: Optional[List[VariantInventoryUpdate]] = Field(None, description="List of inventory records to update")


class ProductSimpleInfo(BaseModel):
    """Simple product info for variant responses"""
    id: int
    name: str
    price: Decimal

    class Config:
        from_attributes = True


class VariantResponse(VariantBase):
    """Response schema for variant with inventory"""
    id: int
    product_id: int
    product: Optional[ProductSimpleInfo] = None
    stock_quantity: int = 0
    available_quantity: int = 0
    is_low_stock: bool = False
    inventory: List[VariantInventoryResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VariantListResponse(BaseModel):
    """Response schema for paginated variant list"""
    items: List[VariantResponse]
    total: int
    page: int
    limit: int
    pages: int


class VariantSearchParams(BaseModel):
    """Search parameters for variants"""
    product_id: Optional[int] = Field(None, description="Filter by product ID")
    search: Optional[str] = Field(None, description="Search by variant name")
    low_stock: Optional[bool] = Field(None, description="Filter variants with low stock")
    page: int = Field(1, ge=1)
    limit: int = Field(20, ge=1, le=100)
    sort_by: Optional[str] = Field("sort_order", pattern="^(variant_name|sku|sort_order|created_at|updated_at)$")
    sort_order: Optional[str] = Field("asc", pattern="^(asc|desc)$")
