from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from math import ceil

from app.database import get_db
from app.models.user import User
from app.schemas.variant import (
    VariantCreateWithInventory,
    VariantUpdateWithInventory,
    VariantResponse,
    VariantListResponse,
    VariantSearchParams,
    VariantInventoryResponse,
    ProductSimpleInfo
)
from app.services.variant_service import VariantService
from app.deps.auth import require_permission
from app.core.exceptions import ValidationError, NotFoundError

router = APIRouter()


def transform_variant_response(variant) -> VariantResponse:
    """Transform variant model to response schema with inventory"""
    # Calculate stock quantities from inventory
    total_stock = sum(inv.stock_quantity for inv in variant.inventory)
    total_available = sum(inv.available_quantity for inv in variant.inventory)
    is_low_stock = any(inv.is_low_stock for inv in variant.inventory)
    
    # Transform product info
    product_info = None
    if variant.product:
        product_info = ProductSimpleInfo(
            id=variant.product.id,
            name=variant.product.name,
            price=variant.product.price
        )
    
    # Transform inventory list
    inventory_list = [
        VariantInventoryResponse.model_validate(inv) for inv in variant.inventory
    ]
    
    return VariantResponse(
        id=variant.id,
        product_id=variant.product_id,
        sku=variant.sku,
        variant_name=variant.variant_name,
        color=variant.color,
        size=variant.size,
        weight=variant.weight,
        additional_price=variant.additional_price,
        sort_order=variant.sort_order,
        product=product_info,
        stock_quantity=total_stock,
        available_quantity=total_available,
        is_low_stock=is_low_stock,
        inventory=inventory_list,
        created_at=variant.created_at,
        updated_at=variant.updated_at
    )


@router.get("/variants", response_model=VariantListResponse)
def list_variants(
    product_id: Optional[int] = Query(None, description="Filter by product ID"),
    search: Optional[str] = Query(None, description="Search by variant name"),
    low_stock: Optional[bool] = Query(None, description="Filter variants with low stock"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("sort_order", description="Sort by field"),
    sort_order: str = Query("asc", description="Sort order (asc/desc)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["variants:read"]))
):
    """
    List all product variants with filters and pagination.
    
    **Filters:**
    - **product_id**: Filter by product ID
    - **search**: Search by variant name (case-insensitive)
    - **low_stock**: Filter variants with low stock (true/false)
    
    **Pagination:**
    - **page**: Page number (default: 1)
    - **limit**: Items per page (default: 20, max: 100)
    
    **Sorting:**
    - **sort_by**: Field to sort by (variant_name, sku, sort_order, created_at, updated_at)
    - **sort_order**: Sort direction (asc, desc)
    
    **Returns:**
    - List of variants with inventory information
    - Total count of matching variants
    - Pagination metadata
    """
    # Create search params
    params = VariantSearchParams(
        product_id=product_id,
        search=search,
        low_stock=low_stock,
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    # Get variants
    variants, total = VariantService.get_all(db, params)
    
    # Calculate total pages
    pages = ceil(total / limit) if total > 0 else 0
    
    # Transform to response
    items = [transform_variant_response(v) for v in variants]
    
    return VariantListResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        pages=pages
    )


@router.post("/variants", response_model=VariantResponse, status_code=status.HTTP_201_CREATED)
def create_variant(
    request: Request,
    product_id: int,
    variant_data: VariantCreateWithInventory,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["variants:create"]))
):
    """
    Create a new product variant with inventory.
    
    **Creates:**
    - Variant record with product attributes
    - One or more inventory records for the variant
    
    **Request Body:**
    ```json
    {
      "product_id": 1,
      "sku": "PROD-RED-M",
      "variant_name": "Red - Medium",
      "color": "Red",
      "size": "M",
      "weight": "1.2kg",
      "additional_price": 5.00,
      "sort_order": 0,
      "inventory": [
        {
          "stock_quantity": 100,
          "reserved_quantity": 0,
          "low_stock_threshold": 10,
          "reorder_level": 5,
          "sku": "PROD-RED-M",
          "batch_number": "BATCH-001",
          "location": "Warehouse A"
        }
      ]
    }
    ```
    
    **Notes:**
    - SKU must be unique across all variants
    - Inventory is optional but recommended
    - Multiple inventory records can be created for different locations
    """
    ip_address = request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or \
                 request.headers.get("X-Real-IP", "") or \
                 (request.client.host if request.client else None)
    user_agent = request.headers.get("User-Agent")
    
    try:
        variant = VariantService.create(
            db=db,
            product_id= product_id,
            variant_data=variant_data,
            current_user=current_user,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Reload with relationships
        variant = VariantService.get_by_id(db, variant.id)
        
        return transform_variant_response(variant)
        
    except (ValidationError, NotFoundError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# ENDPOINT 3: PUT /variants/{variant_id} - Update variant with inventory
# ============================================================================
@router.put("/variants/{variant_id}", response_model=VariantResponse)
def update_variant(
    request: Request,
    variant_id: int,
    variant_data: VariantUpdateWithInventory,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["variants:update"]))
):
    """
    Update a product variant and its inventory.
    
    **Updates:**
    - Variant attributes (name, SKU, color, size, etc.)
    - Existing inventory records or creates new ones
    
    **Request Body:**
    ```json
    {
      "variant_name": "Red - Large",
      "size": "L",
      "additional_price": 7.50,
      "inventory": [
        {
          "stock_quantity": 150,
          "low_stock_threshold": 15,
          "location": "Warehouse B"
        }
      ]
    }
    ```
    
    **Notes:**
    - All fields are optional - only provided fields will be updated
    - If inventory is provided, it updates existing inventory records
    - If more inventory data is provided than exists, new records are created
    """
    ip_address = request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or \
                 request.headers.get("X-Real-IP", "") or \
                 (request.client.host if request.client else None)
    user_agent = request.headers.get("User-Agent")
    
    try:
        variant = VariantService.update(
            db=db,
            variant_id=variant_id,
            variant_data=variant_data,
            current_user=current_user,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        if not variant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Variant with ID {variant_id} not found"
            )
        
        # Reload with relationships
        variant = VariantService.get_by_id(db, variant.id)
        
        return transform_variant_response(variant)
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# ENDPOINT 4: DELETE /variants/{variant_id} - Delete variant and inventory
# ============================================================================
@router.delete("/variants/{variant_id}", status_code=status.HTTP_200_OK)
def delete_variant(
    request: Request,
    variant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["variants:delete"]))
):
    """
    Delete a product variant and its inventory (cascade delete).
    
    **Cascade Behavior:**
    - When a variant is deleted, all associated inventory records are automatically deleted
    - This is handled by the database CASCADE constraint
    
    **Restrictions:**
    - Cannot delete variants that are in existing orders
    - Cannot delete variants currently in shopping carts
    
    **Returns:**
    ```json
    {
      "message": "Variant deleted successfully",
      "deleted_inventory_count": 2
    }
    ```
    """
    ip_address = request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or \
                 request.headers.get("X-Real-IP", "") or \
                 (request.client.host if request.client else None)
    user_agent = request.headers.get("User-Agent")
    
    try:
        # Get variant to count inventory before deletion
        variant = VariantService.get_by_id(db, variant_id)
        if not variant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Variant with ID {variant_id} not found"
            )
        
        inventory_count = len(variant.inventory)
        
        # Delete variant (inventory will cascade delete)
        success = VariantService.delete(
            db=db,
            variant_id=variant_id,
            current_user=current_user,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Variant with ID {variant_id} not found"
            )
        
        return {
            "message": "Variant deleted successfully",
            "deleted_inventory_count": inventory_count
        }
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# BONUS ENDPOINT: GET /variants/{variant_id} - Get single variant details
# ============================================================================
@router.get("/variants/{variant_id}", response_model=VariantResponse)
def get_variant(
    variant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["variants:read"]))
):
    """
    Get a single variant by ID with full details including inventory.
    
    **Returns:**
    - Variant information
    - Product information
    - All inventory records for this variant
    - Calculated stock quantities
    - Low stock status
    """
    variant = VariantService.get_by_id(db, variant_id)
    
    if not variant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Variant with ID {variant_id} not found"
        )
    
    return transform_variant_response(variant)


# ============================================================================
# BONUS ENDPOINT: GET /variants/stats/count - Get variant count
# ============================================================================
@router.get("/variants/stats/count")
def get_variant_count(
    product_id: Optional[int] = Query(None, description="Filter by product ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["variants:read"]))
):
    """
    Get total count of variants with optional product filter.
    
    **Returns:**
    ```json
    {
      "count": 25,
      "product_id": 1
    }
    ```
    """
    count = VariantService.get_variant_count(db, product_id)
    
    return {
        "count": count,
        "product_id": product_id
    } 
