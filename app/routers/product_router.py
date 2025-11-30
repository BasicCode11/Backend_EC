from typing import List, Optional, Union, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, UploadFile, File, Form
from sqlalchemy import null
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
    ProductStatus,
    InventoryCreate,
    BrandSimple,
)
from app.services.product_service import ProductService
from app.services.file_service import LogoUpload
from app.deps.auth import get_current_active_user, require_permission
from app.core.exceptions import ValidationError

router = APIRouter()


def normalize_images(
    images: Any = File(None)
) -> Optional[List[UploadFile]]:
    """Normalize images parameter to always be a list - handles both single file and list of files"""
    if images is None:
        return None
    # Handle single file
    if isinstance(images, UploadFile):
        return [images]
    # Handle list of files
    if isinstance(images, list):
        return images
    # Fallback - wrap in list
    return [images] if images else None


def transform_variant_with_stock(variant):
    """Helper function to transform variant with computed stock_quantity and inventory"""
    from app.schemas.product import ProductVariantResponse, InventoryInVariant
    
    # Get inventory for stock calculation
    variant_inventory = getattr(variant, "inventory", None)
    if variant_inventory is None:
        variant_inventory = []
    elif not hasattr(variant_inventory, '__iter__') or isinstance(variant_inventory, str):
        variant_inventory = []
    else:
        try:
            variant_inventory = list(variant_inventory)
        except (TypeError, AttributeError):
            variant_inventory = []
    
    # Transform inventory list
    inventory_list = [
        InventoryInVariant.model_validate(inv) for inv in variant_inventory
    ]
    
    return ProductVariantResponse(
        id=variant.id,
        product_id=variant.product_id,
        sku=variant.sku,
        variant_name=variant.variant_name,
        color=variant.color,
        size=variant.size,
        weight=variant.weight,
        additional_price=variant.additional_price,
        sort_order=variant.sort_order,
        stock_quantity=sum(inv.stock_quantity for inv in variant_inventory),
        available_quantity=sum(inv.available_quantity for inv in variant_inventory),
        inventory=inventory_list,
        created_at=variant.created_at,
        updated_at=variant.updated_at
    )


def transform_product_with_primary_image(product):
    """Helper function to transform product with primary image, category, and inventory summary"""
    from app.schemas.product import ProductResponse, CategorySimple, InventorySimple
    
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
    
    # Calculate inventory summary from all variants
    total_stock = 0
    total_reserved = 0
    total_available = 0
    low_stock_count = 0
    
    for variant in product.variants:
        variant_inventory = getattr(variant, "inventory", [])
        if variant_inventory and hasattr(variant_inventory, '__iter__') and not isinstance(variant_inventory, str):
            try:
                variant_inventory = list(variant_inventory)
            except (TypeError, AttributeError):
                variant_inventory = []
        else:
            variant_inventory = []
            
        for inv in variant_inventory:
            total_stock += inv.stock_quantity
            total_reserved += inv.reserved_quantity
            total_available += inv.available_quantity
            if inv.is_low_stock:
                low_stock_count += 1
    
    inventory_summary = InventorySimple(
        total_stock=total_stock,
        total_reserved=total_reserved,
        total_available=total_available,
        low_stock_count=low_stock_count
    )
    
    return ProductResponse(
        id=product.id,
        name=product.name,
        description=product.description,
        material=product.material,
        care_instructions=product.care_instructions,
        price=product.price,
        compare_price=product.compare_price,
        cost_price=product.cost_price,
        category_id=product.category_id,
        category=category_obj,
        brand_id=product.brand_id,
        weight=product.weight,
        dimensions=product.dimensions,
        featured=product.featured,
        status=product.status,
        primary_image=primary_img,
        inventory_summary=inventory_summary,
        created_at=product.created_at,
        updated_at=product.updated_at
    )


def transform_product_with_details(product):
    """Transform product with full details including images and variants with nested inventory"""
    from app.schemas.product import (
        ProductWithDetails,
        CategorySimple,
        ProductImageResponse,
        InventorySimple
    )

    # --- Primary Image ---
    primary_img = None
    if product.images:
        for img in product.images:
            if img.is_primary:
                primary_img = img.image_url
                break
        if not primary_img and product.images:
            primary_img = product.images[0].image_url

    # --- Category ---
    category_obj = None
    if product.category:
        category_obj = CategorySimple(
            id=product.category.id,
            name=product.category.name
        )

    # --- Brand ---
    brand_obj = None
    if product.brand:
        brand_obj = BrandSimple(
            id=product.brand.id,
            name=product.brand.name
        )
    # --- Calculate inventory summary from all variants ---
    total_stock = 0
    total_reserved = 0
    total_available = 0
    low_stock_count = 0

    for variant in product.variants:
        variant_inventory = getattr(variant, "inventory", [])
        if variant_inventory and hasattr(variant_inventory, '__iter__') and not isinstance(variant_inventory, str):
            try:
                variant_inventory = list(variant_inventory)
            except (TypeError, AttributeError):
                variant_inventory = []
        else:
            variant_inventory = []
            
        for inv in variant_inventory:
            total_stock += inv.stock_quantity
            total_reserved += inv.reserved_quantity
            total_available += inv.available_quantity
            if inv.is_low_stock:
                low_stock_count += 1

    inventory_summary = InventorySimple(
        total_stock=total_stock,
        total_reserved=total_reserved,
        total_available=total_available,
        low_stock_count=low_stock_count
    )

    # --- Transform variants (use the helper function) ---
    variant_list = [transform_variant_with_stock(v) for v in product.variants]

    # --- Transform product ---
    return ProductWithDetails(
        id=product.id,
        name=product.name,
        description=product.description,
        material=product.material,
        care_instructions=product.care_instructions,
        price=product.price,
        compare_price=product.compare_price,
        cost_price=product.cost_price,
        category_id=product.category_id,
        category=category_obj,
        brand_id=product.brand_id,
        brand=brand_obj,
        weight=product.weight,
        dimensions=product.dimensions,
        featured=product.featured,
        status=product.status,
        primary_image=primary_img,
        inventory_summary=inventory_summary,
        created_at=product.created_at,
        updated_at=product.updated_at,
        images=[ProductImageResponse.model_validate(img) for img in product.images],
        variants=variant_list
    )




@router.get("/products", response_model=ProductListResponse)
def list_products(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[ProductStatus] = None,
    category_id: Optional[int] = None,
    featured: Optional[bool] = None,
    brand_id: Optional[int] = None,
    search: Optional[str] = Query(
        None,
        description="Filter by product name/description/brand (case-insensitive substring match)"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["products:read"]))
):
    """
    List all products with pagination and optional filters.
    
    - **page**: Page number (default: 1)
    - **limit**: Items per page (default: 20, max: 100)
    - **status**: Filter by product status (active, inactive, draft)
    - **category_id**: Filter by category ID
    - **featured**: Filter by featured status
    - **search**: Case-insensitive substring match across name, description, brand
    
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
        featured=featured,
        brand_id=brand_id,
        search=search
    )
    
    pages = ceil(total / limit) if total > 0 else 0
    
    # Transform products to include images, variants, and inventory
    items = [transform_product_with_details(p) for p in products]
    
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
    
    # Transform products to include images, variants, and inventory
    items = [transform_product_with_details(p) for p in products]
    
    return {
        "items": items,
        "total": total,
        "page": params.page,
        "limit": params.limit,
        "pages": pages
    }


@router.get("/products/featured", response_model=List[ProductWithDetails])
def list_featured_products(
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """
    Get featured products for customer view.
    Includes product details with images, inventory, and variants so the
    storefront can display full product information.
    """
    products = ProductService.get_featured_products(db, limit)
    return [transform_product_with_details(p) for p in products]


@router.get("/products/by-category", response_model=List[ProductResponse])
def list_products_by_category(
    category_id: Optional[int] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Get products by category with primary image and category"""
    products = ProductService.get_by_category(db, category_id, limit)
    return [transform_product_with_details(p) for p in products]


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
    material: Optional[str] = Form(None),
    care_instructions: Optional[str] = Form(None),
    compare_price: Optional[Decimal] = Form(None),
    cost_price: Optional[Decimal] = Form(None),
    brand_id: Optional[int] = Form(None),
    weight: Optional[Decimal] = Form(None),
    dimensions: Optional[str] = Form(None),
    featured: bool = Form(False),
    product_status: str = Form("active"),
    inventory: Optional[str] = Form(None),
    variants: Optional[str] = Form(None),
    images: List[UploadFile] = File(None),
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
    - inventory as JSON object string (optional)
    
    Example variants JSON:
    [
        {
            "sku": "DD-RED-M",
            "variant_name": "Red - Medium",
            "color": "Red",
            "size": "M",
            "weight": "0.3",
            "additional_price": 0,
            "sort_order": 1
        },
    ]
    
    Example inventory JSON:
    [
      {
        "sku": "DD-RED-M",
        "stock_quantity": 100,
        "reserved_quantity": 0,
        "low_stock_threshold": 10,
        "reorder_level": 5,
        "batch_number": "BATCH-2024-001",
        "location": "Warehouse A"
        }
    ]
    
    NOTE: Stock is managed via inventory. You can create inventory during product creation
    or use /api/inventory endpoints to manage stock separately.
    
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
                raise HTTPException(status_code=400, detail="Invalid JSON format for dimensions")
        # Parse inventory JSON if provided (supports single object or list)
        inventory_list = []
        if inventory:
            try:
                parsed_inventory = json.loads(inventory)
            
            except json.JSONDecodeError as e:
                raise HTTPException(status_code=400, detail=f"Invalid JSON format for inventory: {str(e)}")

            if isinstance(parsed_inventory, dict):
                parsed_inventory = [parsed_inventory]
            elif isinstance(parsed_inventory, list):
                if not all(isinstance(item, dict) for item in parsed_inventory):
                    raise HTTPException(status_code=400, detail="Each inventory entry must be an object")
            else:
                raise HTTPException(status_code=400, detail="Inventory must be a JSON object or array of objects")

            for inventory_item in parsed_inventory:
                inventory_list.append(InventoryCreate(**inventory_item))
            
        # Parse variants JSON if provided
        variant_data_list = []
        if variants:
            try:
                variants_list = json.loads(variants)
                if not isinstance(variants_list, list):
                    raise HTTPException(status_code=400, detail="Variants must be a JSON array")
                
                for idx, variant_item in enumerate(variants_list):
                    variant_data_list.append(
                        ProductVariantCreate(
                            sku=variant_item.get("sku"),
                            variant_name=variant_item.get("variant_name"),
                            color=variant_item.get("color"),
                            size=variant_item.get("size"),
                            weight=variant_item.get("weight"),
                            additional_price= variant_item.get("additional_price"),
                            sort_order=variant_item.get("sort_order", 0)
                        )
                    )
            except json.JSONDecodeError as e:
                raise HTTPException(status_code=400, detail=f"Invalid JSON format for variants: {str(e)}")
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error parsing variants: {str(e)}")
        
        # Upload images and create image data
        image_data_list = []
        if images:
            for idx, image_file in enumerate(images):
                if image_file.filename:  # Check if file is actually uploaded
                    cloud = LogoUpload._save_image(image_file)
                    image_data_list.append(
                        ProductImageCreate(
                            image_url=cloud["url"],
                            image_public_id=cloud["public_id"],
                            alt_text=f"{name} image {idx + 1}",
                            sort_order=idx,
                            is_primary=(idx == 0)  # First image is primary
                        )
                    )
        
        # Create product data object
        product_data = ProductCreate(
            name=name,
            description=description,
            material=material,
            care_instructions=care_instructions,
            price=price,
            compare_price=compare_price,
            cost_price=cost_price,
            category_id=category_id,
            brand_id=brand_id,
            weight=weight,
            dimensions=dimensions_dict,
            featured=featured,
            status=ProductStatus(product_status),
            images=image_data_list,
            variants=variant_data_list,
            inventory=inventory_list
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


@router.put("/products/{product_id}", response_model=ProductWithDetails)
def update_product(
    request: Request,
    product_id: int,
    name: Optional[str] = Form(None),
    price: Optional[Decimal] = Form(None),
    category_id: Optional[int] = Form(None),
    description: Optional[str] = Form(None),
    material: Optional[str] = Form(None),
    care_instructions: Optional[str] = Form(None),
    compare_price: Optional[Decimal] = Form(None),
    cost_price: Optional[Decimal] = Form(None),
    brand_id: Optional[int] = Form(None),
    weight: Optional[Decimal] = Form(None),
    dimensions: Optional[str] = Form(None),
    featured: bool = Form(True),
    status: ProductStatus = Form(ProductStatus.ACTIVE),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["products:update"]))
):
    """
    Update a product - requires products:update permission.
    
    All fields are optional. Only provided fields will be updated.
    Accepts multipart/form-data.
    
    - **images**: Multiple image files to replace all existing product images. 
      If provided, all old images will be deleted and replaced with new ones.
      If not provided, existing images remain unchanged.
    - **status**: Product status (active, inactive, draft)
    
    Note: To delete individual images, use the DELETE /api/products/images/{image_id} endpoint.
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
            material=material,
            care_instructions=care_instructions,
            price=price,
            compare_price=compare_price,
            cost_price=cost_price,
            category_id=category_id,
            brand_id=brand_id,
            weight=weight,
            dimensions=dimensions_dict,
            featured=featured,
            status=ProductStatus(status),
        )
        
        # Update product
        product = ProductService.update(db, product_id, product_data, current_user, ip_address, user_agent)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        product = ProductService.get_with_details(db, product.id)
        
        return transform_product_with_details(product)
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
        cloud = LogoUpload._save_image(image)
        
        # Create image data
        image_data = ProductImageCreate(
            image_url=cloud["url"],
            image_public_id=cloud["public_id"],
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

