from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from math import ceil

from app.database import get_db
from app.schemas.catalog import CatalogResponse
from app.services.product_service import ProductService
from app.services.category_service import CategoryService
from app.services.brand_service import BrandService

router = APIRouter()

@router.get(
    "/catalog",
    response_model=CatalogResponse,
    summary="Get public-facing product catalog",
    description="Fetches a paginated list of active products, and all active categories and brands to be used for display and filtering on a customer-facing website.",
    tags=["Catalog"]
)
def get_catalog(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number for product pagination."),
    limit: int = Query(20, ge=1, le=100, description="Number of products to return per page."),
    category_id: Optional[int] = Query(None, description="Filter products by a specific category ID."),
    brand_id: Optional[int] = Query(None, description="Filter products by a specific brand ID."),
    search: Optional[str] = Query(None, description="Search term to filter products by name or description."),
):
    """
    This endpoint serves the main product catalog. It provides:
    - A paginated list of **active** products.
    - Filtering options for products (category, brand, search).
    - A complete list of all **active** categories for building filter menus.
    - A complete list of all **active** brands for building filter menus.
    """
    # Get paginated products based on filters
    skip = (page - 1) * limit
    products, total_products = ProductService.get_all(
        db,
        skip=skip,
        limit=limit,
        status="active",  # Only show active products to customers
        category_id=category_id,
        brand_id=brand_id,
        search=search,
    )

    # Get all active categories for filtering UI
    # We get all of them (with a high limit) because the frontend will need the full list to build filter options.
    categories = CategoryService.get_all(db, is_active=True, limit=1000)

    # Get all active brands for filtering UI
    brands, _ = BrandService.get_all(db, status="active", limit=1000)

    # Calculate total pages for product pagination
    pages = ceil(total_products / limit) if total_products > 0 else 1

    return {
        "items": products,
        "categories": categories,
        "brands": brands,
        "total": total_products,
        "page": page,
        "limit": limit,
        "pages": pages,
    }
