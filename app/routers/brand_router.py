from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from math import ceil
from app.database import get_db
from app.models.user import User
from app.schemas.brand import (
    BrandCreate,
    BrandUpdate,
    BrandResponse,
    BrandWithProducts,
    BrandListResponse
)
from app.services.brand_service import BrandService
from app.deps.auth import get_current_active_user, require_permission
from app.core.exceptions import ValidationError

router = APIRouter()


@router.get("/brands", response_model=BrandListResponse)
def list_brands(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=500, description="Items per page"),
    status: Optional[str] = Query(None, pattern="^(active|inactive)$", description="Filter by status"),
    search: Optional[str] = Query(None, description="Search by brand name"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["brands:read"]))
):
    """
    List all brands with optional filters.
    
    - **page**: Page number for pagination
    - **limit**: Maximum number of records to return
    - **status**: Filter by brand status (active/inactive)
    - **search**: Search brands by name
    """
    brands, total = BrandService.get_all(
        db=db,
        page=page,
        limit=limit,
        status=status,
        search=search
    )
    
    pages = ceil(total / limit) if total > 0 else 0
    
    return {
        "brands": brands,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages
    }



@router.get("/brands/{brand_id}", response_model=BrandResponse)
def get_brand(
    brand_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["brands:read"]))
):
    """Get a specific brand by ID"""
    brand = BrandService.get_by_id(db, brand_id)
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brand not found"
        )
    return brand


@router.get("/brands/{brand_id}/with-products", response_model=BrandWithProducts)
def get_brand_with_product_count(
    brand_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["brands:read"]))
):
    """Get a brand with product count"""
    brand = BrandService.get_by_id(db, brand_id)
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brand not found"
        )
    
    # Add product count
    brand_dict = {
        **brand.__dict__,
        "product_count": len(brand.products)
    }
    return brand_dict


@router.post("/brands", response_model=BrandResponse, status_code=status.HTTP_201_CREATED)
def create_brand(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    logo: UploadFile = File(...),
    status: str = Form(default="active", pattern="^(active|inactive)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["brands:create"]))
):
    """
    Create a new brand - requires brands:create permission.
    
    - **name**: Brand name (required)
    - **description**: Brand description (optional)
    - **logo**: Brand logo image (required)
    - **status**: Brand status - active or inactive (default: active)
    """
    brand_data = BrandCreate(
        name=name,
        description=description,
        status=status
    )
    try:
        brand = BrandService.create(db, current_user, brand_data, logo)
        return brand
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/brands/{brand_id}", response_model=BrandResponse)
def update_brand(
    brand_id: int,
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    logo: Optional[UploadFile] = File(None),
    status: Optional[str] = Form(None, pattern="^(active|inactive)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["brands:update"]))
):
    """
    Update a brand - requires brands:update permission.
    
    All fields are optional. Only provided fields will be updated.
    """
    try:
        brand_data = BrandUpdate(
            name=name,
            description=description,
            status=status
        )
        brand = BrandService.update(db, brand_id, brand_data, current_user, logo)
        if not brand:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Brand not found"
            )
        return brand
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/brands/{brand_id}", status_code=status.HTTP_200_OK)
def delete_brand(
    brand_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["brands:delete"]))
):
    """
    Delete a brand - requires brands:delete permission.
    
    Note: Cannot delete brands that have associated products.
    """
    try:
        success = BrandService.delete(db, brand_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Brand not found"
            )
        return {"message": "Brand deleted successfully"}
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
