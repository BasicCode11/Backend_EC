from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, UploadFile, File, Form
from sqlalchemy.orm import Session
from math import ceil
from decimal import Decimal
import json
from app.database import get_db
from app.models.user import User
from app.models.product_variant import ProductVariant
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
from app.services.file_service import LogoUpload
from app.deps.auth import get_current_active_user, require_permission
from app.core.exceptions import ValidationError

router = APIRouter()


def transform_product_with_primary_image(product):
    """Helper function to transform product with primary image and category"""
    from app.schemas.product import ProductResponse, CategorySimple
    
    # Get primary image URL
    primary_img = None
    if product.images:
        for img in product.images:
            if img.is_primary:
                primary_img = img.image_url
                break
        if not primary_img and product.images:
            primary_img = product.images[0].image_url
    
    # Create category object
    category_obj = None
    if product.category:
        category_obj = CategorySimple(
            id=product.category.id,
            name=product.category.name
        )
    
    return ProductResponse(
        id=product.id,
        name=product.name,
        description=product.description,
        price=product.price,
        compare_price=product.compare_price,
        cost_price=product.cost_price,
        category_id=product.category_id,
        category=category_obj,
        brand=product.brand,
        weight=product.weight,
        dimensions=product.dimensions,
        featured=product.featured,
        status=product.status,
        primary_image=primary_img,
        created_at=product.created_at,
        updated_at=product.updated_at
    )


def transform_product_with_details(product):
    """Helper function to transform product with full details including images and variants"""
    from app.schemas.product import ProductWithDetails, CategorySimple, ProductImageResponse, ProductVariantResponse
    
    # Get primary image URL
    primary_img = None
    if product.images:
        for img in product.images:
            if img.is_primary:
                primary_img = img.image_url
                break
        if not primary_img and product.images:
            primary_img = product.images[0].image_url
    
    # Create category object
    category_obj = None
    if product.category:
        category_obj = CategorySimple(
            id=product.category.id,
            name=product.category.name
        )
    
    return ProductWithDetails(
        id=product.id,
        name=product.name,
        description=product.description,
        price=product.price,
        compare_price=product.compare_price,
        cost_price=product.cost_price,
        category_id=product.category_id,
        category=category_obj,
        brand=product.brand,
        weight=product.weight,
        dimensions=product.dimensions,
        featured=product.featured,
        status=product.status,
        primary_image=primary_img,
        created_at=product.created_at,
        updated_at=product.updated_at,
        images=[ProductImageResponse.model_validate(img) for img in product.images],
        variants=[ProductVariantResponse.model_validate(v) for v in product.variants]
    )


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
    
    Returns products with primary_image and category object.
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
    
    # Transform products to include primary_image and category
    items = [transform_product_with_primary_image(p) for p in products]
    
    return {
        "items": items,
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
    
    # Transform products to include primary_image and category
    items = [transform_product_with_primary_image(p) for p in products]
    
    return {
        "items": items,
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
    """Get featured products with primary image and category"""
    products = ProductService.get_featured_products(db, limit)
    return [transform_product_with_primary_image(p) for p in products]


@router.get("/products/by-category/{category_id}", response_model=List[ProductResponse])
def list_products_by_category(
    category_id: int,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Get products by category with primary image and category"""
    products = ProductService.get_by_category(db, category_id, limit)
    return [transform_product_with_primary_image(p) for p in products]


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
    
    return transform_product_with_details(product)


@router.post("/products", response_model=ProductWithDetails, status_code=status.HTTP_201_CREATED)
def create_product(
    request: Request,
    name: str = Form(...),
    price: Decimal = Form(...),
    category_id: int = Form(...),
    description: Optional[str] = Form(None),
    compare_price: Optional[Decimal] = Form(None),
    cost_price: Optional[Decimal] = Form(None),
    brand: Optional[str] = Form(None),
    weight: Optional[Decimal] = Form(None),
    dimensions: Optional[str] = Form(None),
    featured: bool = Form(False),
    product_status: str = Form("active"),
    variants: Optional[str] = Form(None),
    images: List[UploadFile] = File(None),
    variant_images: Optional[List[UploadFile]] = File(default=[]),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["products:create"]))
):
    """
    Create a new product - requires products:create permission.
    
    Accepts multipart/form-data with:
    - Basic product fields
    - Multiple image file uploads (for main product images)
    - Multiple variant_images file uploads (for variant-specific images, matched by index)
    - dimensions as JSON string (optional)
    - variants as JSON array string (optional)
    
    Example variants JSON:
    [
      {
        "sku": "PROD-RED-M",
        "variant_name": "Red - Medium",
        "attributes": {"color": "Red", "size": "M"},
        "price": 29.99,
        "sort_order": 0
      }
    ]
    
    NOTE: Stock is NOT managed via variants. After creating the product,
    use /api/inventory endpoints to manage stock for the product.
    
    Note: variant_images are matched to variants by index order.
    First variant_images file goes to first variant, second to second variant, etc.
    """
    ip_address = request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or request.headers.get("X-Real-IP", "") or (request.client.host if request.client else None)
    user_agent = request.headers.get("User-Agent")
    
    try:
        # Parse dimensions JSON if provided
        dimensions_dict = None
        if dimensions:
            try:
                dimensions_dict = json.loads(dimensions)
            except json.JSONDecodeError:
                raise ValidationError("Invalid JSON format for dimensions")
        
        # Parse variants JSON if provided
        variant_data_list = []
        if variants:
            try:
                variants_list = json.loads(variants)
                if not isinstance(variants_list, list):
                    raise ValidationError("Variants must be a JSON array")
                
                for idx, variant_item in enumerate(variants_list):
                    # Check if there's a corresponding variant image file
                    variant_image_url = variant_item.get("image_url")
                    if variant_images and idx < len(variant_images):
                        variant_image_file = variant_images[idx]
                        if variant_image_file.filename:
                            variant_image_url = LogoUpload._save_image(variant_image_file)
                    
                    variant_data_list.append(
                        ProductVariantCreate(
                            sku=variant_item.get("sku"),
                            variant_name=variant_item.get("variant_name"),
                            attributes=variant_item.get("attributes"),
                            price=variant_item.get("price"),
                            image_url=variant_image_url,
                            sort_order=variant_item.get("sort_order", 0)
                        )
                    )
            except json.JSONDecodeError as e:
                raise ValidationError(f"Invalid JSON format for variants: {str(e)}")
            except Exception as e:
                raise ValidationError(f"Error parsing variants: {str(e)}")
        
        # Upload images and create image data
        image_data_list = []
        if images:
            for idx, image_file in enumerate(images):
                if image_file.filename:  # Check if file is actually uploaded
                    image_url = LogoUpload._save_image(image_file)
                    image_data_list.append(
                        ProductImageCreate(
                            image_url=image_url,
                            alt_text=f"{name} image {idx + 1}",
                            sort_order=idx,
                            is_primary=(idx == 0)  # First image is primary
                        )
                    )
        
        # Create product data object
        product_data = ProductCreate(
            name=name,
            description=description,
            price=price,
            compare_price=compare_price,
            cost_price=cost_price,
            category_id=category_id,
            brand=brand,
            weight=weight,
            dimensions=dimensions_dict,
            featured=featured,
            status=ProductStatus(product_status),
            images=image_data_list,
            variants=variant_data_list
        )
        
        product = ProductService.create(db, product_data, current_user, ip_address, user_agent)
        # Reload with details
        product = ProductService.get_with_details(db, product.id)
        return transform_product_with_details(product)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/products/{product_id}", response_model=ProductResponse)
def update_product(
    request: Request,
    product_id: int,
    name: Optional[str] = Form(None),
    price: Optional[Decimal] = Form(None),
    category_id: Optional[int] = Form(None),
    description: Optional[str] = Form(None),
    compare_price: Optional[Decimal] = Form(None),
    cost_price: Optional[Decimal] = Form(None),
    brand: Optional[str] = Form(None),
    weight: Optional[Decimal] = Form(None),
    dimensions: Optional[str] = Form(None),
    featured: Optional[bool] = Form(None),
    product_status: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["products:update"]))
):
    """
    Update a product - requires products:update permission.
    
    All fields are optional. Only provided fields will be updated.
    Accepts multipart/form-data.
    """
    ip_address = request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or request.headers.get("X-Real-IP", "") or (request.client.host if request.client else None)
    user_agent = request.headers.get("User-Agent")
    try:
        # Parse dimensions JSON if provided
        dimensions_dict = None
        if dimensions:
            try:
                dimensions_dict = json.loads(dimensions)
            except json.JSONDecodeError:
                raise ValidationError("Invalid JSON format for dimensions")
        
        # Create update data object
        product_data = ProductUpdate(
            name=name,
            description=description,
            price=price,
            compare_price=compare_price,
            cost_price=cost_price,
            category_id=category_id,
            brand=brand,
            weight=weight,
            dimensions=dimensions_dict,
            featured=featured,
            status=ProductStatus(product_status) if product_status else None
        )
        
        product = ProductService.update(db, product_id, product_data, current_user, ip_address, user_agent)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        return transform_product_with_primary_image(product)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/products/{product_id}", status_code=status.HTTP_200_OK)
def delete_product(
    request: Request,
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["products:delete"]))
):
    """
    Delete a product - requires products:delete permission.
    
    Note: Cannot delete products with existing orders.
    """
    ip_address = request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or request.headers.get("X-Real-IP", "") or (request.client.host if request.client else None)
    user_agent = request.headers.get("User-Agent")
    try:
        success = ProductService.delete(db, product_id , current_user , ip_address , user_agent)
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
    image: UploadFile = File(...),
    alt_text: Optional[str] = Form(None),
    sort_order: int = Form(0),
    is_primary: bool = Form(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["products:update"]))
):
    """
    Add an image to a product - requires products:update permission.
    
    Upload an image file with optional metadata.
    """
    try:
        # Upload the image file
        image_url = LogoUpload._save_image(image)
        
        # Create image data
        image_data = ProductImageCreate(
            image_url=image_url,
            alt_text=alt_text,
            sort_order=sort_order,
            is_primary=is_primary
        )
        
        image_record = ProductService.add_image(db, product_id, image_data)
        return image_record
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
    variant_name: str = Form(...),
    sku: Optional[str] = Form(None),
    attributes: Optional[str] = Form(None),
    price: Optional[Decimal] = Form(None),
    sort_order: int = Form(0),
    variant_image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["products:update"]))
):
    """
    Add a variant to a product - requires products:update permission.
    
    Accepts multipart/form-data with:
    - variant_name (required)
    - sku, price, sort_order (optional)
    - attributes as JSON string (optional)
    - variant_image file upload (optional)
    
    NOTE: Stock is NOT managed here. Use /api/inventory endpoints to manage stock.
    Variants define product options (size, color, etc.) and optional pricing.
    """
    try:
        # Parse attributes JSON if provided
        attributes_dict = None
        if attributes:
            try:
                attributes_dict = json.loads(attributes)
            except json.JSONDecodeError:
                raise ValidationError("Invalid JSON format for attributes")
        
        # Upload variant image if provided
        image_url_str = None
        if variant_image and variant_image.filename:
            image_url_str = LogoUpload._save_image(variant_image)
        
        # Create variant data object
        variant_data = ProductVariantCreate(
            sku=sku,
            variant_name=variant_name,
            attributes=attributes_dict,
            price=price,
            image_url=image_url_str,
            sort_order=sort_order
        )
        
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
    variant_name: Optional[str] = Form(None),
    sku: Optional[str] = Form(None),
    attributes: Optional[str] = Form(None),
    price: Optional[Decimal] = Form(None),
    sort_order: Optional[int] = Form(None),
    variant_image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["products:update"]))
):
    """
    Update a product variant - requires products:update permission.
    
    Accepts multipart/form-data with optional fields:
    - variant_name, sku, price, sort_order
    - attributes as JSON string
    - variant_image file upload (will replace existing image)
    
    NOTE: Stock is NOT managed here. Use /api/inventory endpoints to manage stock.
    """
    try:
        # Parse attributes JSON if provided
        attributes_dict = None
        if attributes:
            try:
                attributes_dict = json.loads(attributes)
            except json.JSONDecodeError:
                raise ValidationError("Invalid JSON format for attributes")
        
        # Upload new variant image if provided
        image_url_str = None
        if variant_image and variant_image.filename:
            # Get old variant to delete old image
            old_variant = db.get(ProductVariant, variant_id)
            if old_variant and old_variant.image_url:
                LogoUpload._delete_logo(old_variant.image_url)
            
            image_url_str = LogoUpload._save_image(variant_image)
        
        # Create update data object
        variant_data = ProductVariantUpdate(
            sku=sku,
            variant_name=variant_name,
            attributes=attributes_dict,
            price=price,
            image_url=image_url_str,
            sort_order=sort_order
        )
        
        variant = ProductService.update_variant(db, variant_id, variant_data)
        if not variant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Variant not found"
            )
        return variant
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/products/variants/{variant_id}", status_code=status.HTTP_200_OK)
def delete_product_variant(
    variant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["products:update"]))
):
    """
    Delete a product variant - requires products:update permission.
    
    Also deletes the variant image from filesystem if it exists.
    """
    # Get variant to delete its image
    variant = db.get(ProductVariant, variant_id)
    if not variant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Variant not found"
        )
    
    # Delete variant image from filesystem if exists
    if variant.image_url:
        LogoUpload._delete_logo(variant.image_url)
    
    # Delete variant from database
    success = ProductService.delete_variant(db, variant_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Variant not found"
        )
    
    return {"message": "Variant deleted successfully"}
