from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from enum import Enum

class ProductStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"


# Product Image Schemas
class ProductImageBase(BaseModel):
    image_url: str = Field(..., max_length=500)
    image_public_id: Optional[str] = Field(None, max_length=255)
    alt_text: Optional[str] = Field(None, max_length=255)
    sort_order: int = 0
    is_primary: bool = False


class ProductImageCreate(ProductImageBase):
    pass


class ProductImageResponse(ProductImageBase):
    id: int
    product_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Product Variant Schemas
class ProductVariantBase(BaseModel):
    """
    Base schema for Product Variants.
    
    NOTE: stock_quantity is stored on variants but must not exceed product inventory.
    Variants define options (size, color), pricing, and their allocated stock.
    """
    sku: Optional[str] = Field(None, max_length=100)
    variant_name: str = Field(..., max_length=255)
    attributes: Optional[Dict[str, Any]] = None
    price: Optional[Decimal] = Field(None, ge=0)
    image_url: Optional[str] = Field(None, max_length=500)
    image_public_id: Optional[str] = Field(None, max_length=255)
    sort_order: int = 0


class ProductVariantCreate(ProductVariantBase):
    """Schema for creating a new product variant with optional stock"""
    stock_quantity: int = Field(default=0, ge=0, description="Stock for this variant (must not exceed product inventory)")


class ProductVariantUpdate(BaseModel):
    """Schema for updating a product variant (all fields optional)"""
    sku: Optional[str] = Field(None, max_length=100)
    variant_name: Optional[str] = Field(None, max_length=255)
    attributes: Optional[Dict[str, Any]] = None
    price: Optional[Decimal] = Field(None, ge=0)
    stock_quantity: Optional[int] = Field(None, ge=0, description="Stock for this variant (must not exceed product inventory)")
    image_url: Optional[str] = Field(None, max_length=500)
    sort_order: Optional[int] = None


class ProductVariantResponse(ProductVariantBase):
    """
    Response schema for product variants.
    Includes computed stock_quantity from Inventory table.
    """
    id: int
    product_id: int
    stock_quantity: int = Field(default=0, description="Computed from Inventory table")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Product Schemas
class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    price: Decimal = Field(..., ge=0)
    compare_price: Optional[Decimal] = Field(None, ge=0)
    cost_price: Optional[Decimal] = Field(None, ge=0)
    category_id: int
    brand: Optional[str] = Field(None, max_length=100)
    weight: Optional[Decimal] = Field(None, ge=0)
    dimensions: Optional[Dict[str, Any]] = None
    featured: bool = False
    status: ProductStatus = ProductStatus.ACTIVE


class InventoryCreate(BaseModel):
    stock_quantity: int = Field(0, ge=0)
    reserved_quantity: int = Field(0, ge=0)
    low_stock_threshold: int = Field(10, ge=0)
    reorder_level: int = Field(5, ge=0)
    sku: Optional[str] = Field(None, max_length=100)
    batch_number: Optional[str] = Field(None, max_length=100)
    expiry_date: Optional[datetime] = None
    location: Optional[str] = Field(None, max_length=100)


class ProductCreate(ProductBase):
    images: List[ProductImageCreate] = Field(default_factory=list)
    variants: List[ProductVariantCreate] = Field(default_factory=list)
    inventory: List[InventoryCreate] = Field(default_factory=list)

    @field_validator("inventory", mode="before")
    @classmethod
    def ensure_inventory_list(cls, v):
        if v is None:
            return []
        if isinstance(v, dict):
            return [v]
        return v


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, ge=0)
    compare_price: Optional[Decimal] = Field(None, ge=0)
    cost_price: Optional[Decimal] = Field(None, ge=0)
    category_id: Optional[int] = None
    brand: Optional[str] = Field(None, max_length=100)
    weight: Optional[Decimal] = Field(None, ge=0)
    dimensions: Optional[Dict[str, Any]] = None
    featured: Optional[bool] = None
    status: Optional[ProductStatus] = None


class CategorySimple(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class InventorySimple(BaseModel):
    """Simple inventory information for product responses"""
    id: int
    stock_quantity: int
    reserved_quantity: int
    available_quantity: int
    low_stock_threshold: int
    reorder_level: int
    is_low_stock: bool
    needs_reorder: bool
    sku: Optional[str] = None
    location: Optional[str] = None

    class Config:
        from_attributes = True


class ProductResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: Decimal
    compare_price: Optional[Decimal] = None
    cost_price: Optional[Decimal] = None
    category_id: int
    category: Optional[CategorySimple] = None
    brand: Optional[str] = None
    weight: Optional[Decimal] = None
    dimensions: Optional[Dict[str, Any]] = None
    featured: bool
    status: str
    primary_image: Optional[str] = None
    inventory: Optional[List[InventorySimple]] = []
    total_stock: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductWithDetails(ProductResponse):
    images: List[ProductImageResponse] = []
    variants: List[ProductVariantResponse] = []

    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    items: List[ProductWithDetails]
    total: int
    page: int
    limit: int
    pages: int


class ProductSearchParams(BaseModel):
    search: Optional[str] = None
    category_id: Optional[int] = None
    brand: Optional[str] = None
    status: Optional[ProductStatus] = None
    featured: Optional[bool] = None
    min_price: Optional[Decimal] = Field(None, ge=0)
    max_price: Optional[Decimal] = Field(None, ge=0)
    page: int = Field(1, ge=1)
    limit: int = Field(20, ge=1, le=100)
    sort_by: Optional[str] = Field(None, pattern="^(name|price|created_at|updated_at)$")
    sort_order: Optional[str] = Field("asc", pattern="^(asc|desc)$")
