from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query , Request
from sqlalchemy.orm import Session
from math import ceil
from app.database import get_db
from app.models.user import User
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductWithDetails,
    ProductListResponse,
    ProductSearchParams,
    ProductImageCreate,
    ProductImageResponse,
    ProductVariantCreate,
    ProductVariantUpdate,
    ProductVariantResponse,
    ProductStatus
)
from app.services.product_service import ProductService
from app.deps.auth import get_current_active_user, require_permission
from app.core.exceptions import ValidationError

router = APIRouter()


@router.get("/products", response_model=ProductListResponse)
def list_products(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[ProductStatus] = None,
    category_id: Optional[int] = None,
    featured: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    """
    List all products with pagination and optional filters.
    
    - **page**: Page number (default: 1)
    - **limit**: Items per page (default: 20, max: 100)
    - **status**: Filter by product status (active, inactive, draft)
    - **category_id**: Filter by category ID
    - **featured**: Filter by featured status
    """
    skip = (page - 1) * limit
    status_value = status.value if status else None
    
    products, total = ProductService.get_all(
        db=db,
        skip=skip,
        limit=limit,
        status=status_value,
        category_id=category_id,
        featured=featured
    )
    
    pages = ceil(total / limit) if total > 0 else 0
    
    return {
        "items": products,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages
    }


@router.post("/products/search", response_model=ProductListResponse)
def search_products(
    params: ProductSearchParams,
    db: Session = Depends(get_db),
):
    """
    Advanced product search with multiple filters.
    
    Request body supports:
    - **search**: Text search in name, description, brand
    - **category_id**: Filter by category
    - **brand**: Filter by brand name
    - **status**: Filter by status
    - **featured**: Filter by featured status
    - **min_price/max_price**: Price range filter
    - **sort_by**: Sort by field (name, price, created_at, updated_at)
    - **sort_order**: Sort direction (asc, desc)
    - **page**: Page number
    - **limit**: Items per page
    """
    products, total = ProductService.search(db, params)
    pages = ceil(total / params.limit) if total > 0 else 0
    
    return {
        "items": products,
        "total": total,
        "page": params.page,
        "limit": params.limit,
        "pages": pages
    }


@router.get("/products/featured", response_model=List[ProductResponse])
def list_featured_products(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Get featured products"""
    products = ProductService.get_featured_products(db, limit)
    return products


@router.get("/products/by-category/{category_id}", response_model=List[ProductResponse])
def list_products_by_category(
    category_id: int,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Get products by category"""
    products = ProductService.get_by_category(db, category_id, limit)
    return products


@router.get("/products/stats/count")
def get_product_count(
    status: Optional[ProductStatus] = None,
    category_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["products:read"]))
):
    """Get product count - requires products:read permission"""
    status_value = status.value if status else None
    count = ProductService.get_product_count(db, status_value, category_id)
    return {"count": count, "status": status, "category_id": category_id}


@router.get("/products/{product_id}", response_model=ProductWithDetails)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific product by ID with images and variants"""
    product = ProductService.get_with_details(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return product


@router.post("/products", response_model=ProductWithDetails, status_code=status.HTTP_201_CREATED)
def create_product(
    request: Request,
    product_data: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["products:create"]))
):
    """
    Create a new product - requires products:create permission.
    
    Can include images and variants in the request body.
    """
    ip_address = request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or request.headers.get("X-Real-IP", "") or (request.client.host if request.client else None)
    user_agent = request.headers.get("User-Agent")
    try:
        product = ProductService.create(db, product_data , current_user , ip_address , user_agent)
        # Reload with details
        product = ProductService.get_with_details(db, product.id)
        return product
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/products/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    product_data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["products:update"]))
):
    """
    Update a product - requires products:update permission.
    
    All fields are optional. Only provided fields will be updated.
    """
    try:
        product = ProductService.update(db, product_id, product_data)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        return product
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/products/{product_id}", status_code=status.HTTP_200_OK)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["products:delete"]))
):
    """
    Delete a product - requires products:delete permission.
    
    Note: Cannot delete products with existing orders.
    """
    try:
        success = ProductService.delete(db, product_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        return {"message": "Product deleted successfully"}
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# Product Image Endpoints
@router.post("/products/{product_id}/images", response_model=ProductImageResponse, status_code=status.HTTP_201_CREATED)
def add_product_image(
    product_id: int,
    image_data: ProductImageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["products:update"]))
):
    """Add an image to a product - requires products:update permission"""
    try:
        image = ProductService.add_image(db, product_id, image_data)
        return image
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/products/images/{image_id}", status_code=status.HTTP_200_OK)
def delete_product_image(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["products:update"]))
):
    """Delete a product image - requires products:update permission"""
    success = ProductService.delete_image(db, image_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    return {"message": "Image deleted successfully"}


# Product Variant Endpoints
@router.post("/products/{product_id}/variants", response_model=ProductVariantResponse, status_code=status.HTTP_201_CREATED)
def add_product_variant(
    product_id: int,
    variant_data: ProductVariantCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["products:update"]))
):
    """Add a variant to a product - requires products:update permission"""
    try:
        variant = ProductService.add_variant(db, product_id, variant_data)
        return variant
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/products/variants/{variant_id}", response_model=ProductVariantResponse)
def update_product_variant(
    variant_id: int,
    variant_data: ProductVariantUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["products:update"]))
):
    """Update a product variant - requires products:update permission"""
    variant = ProductService.update_variant(db, variant_id, variant_data)
    if not variant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Variant not found"
        )
    return variant


@router.delete("/products/variants/{variant_id}", status_code=status.HTTP_200_OK)
def delete_product_variant(
    variant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["products:update"]))
):
    """Delete a product variant - requires products:update permission"""
    success = ProductService.delete_variant(db, variant_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Variant not found"
        )
    return {"message": "Variant deleted successfully"}
