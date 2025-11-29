from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query , UploadFile , File , Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.category import (
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
    CategoryWithChildren,
    CategoryWithParent
)
from app.services.category_service import CategoryService
from app.deps.auth import get_current_active_user, require_permission
from app.core.exceptions import ValidationError

router = APIRouter()


@router.get("/categories", response_model=List[CategoryResponse])
def list_categories(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1,le=500 , description="Items per page"),
    is_active: Optional[bool] = None,
    parent_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["categories:read"]))
):
    """
    List all categories with optional filters.
    
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    - **is_active**: Filter by active status
    - **parent_id**: Filter by parent category ID (use 0 for root categories)
    """
    if parent_id == 0:
        parent_id = None
    
    categories = CategoryService.get_all(
        db=db,
        page=page,
        limit=limit,
        is_active=is_active,
        parent_id=parent_id
    )
    return categories


@router.get("/categories/root", response_model=List[CategoryResponse])
def list_root_categories(
    db: Session = Depends(get_db),
):
    """Get all root categories (categories without parent)"""
    categories = CategoryService.get_root_categories(db)
    return categories


@router.get("/categories/{category_id}", response_model=CategoryResponse)
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific category by ID"""
    category = CategoryService.get_by_id(db, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    return category


@router.get("/categories/{category_id}/with-children", response_model=CategoryWithChildren)
def get_category_with_children(
    category_id: int,
    db: Session = Depends(get_db),
):
    """Get a category with its direct children"""
    category = CategoryService.get_with_children(db, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    return category


@router.get("/categories/{category_id}/with-parent", response_model=CategoryWithParent)
def get_category_with_parent(
    category_id: int,
    db: Session = Depends(get_db),
):
    """Get a category with its parent"""
    category = CategoryService.get_with_parent(db, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    return category


@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    parent_id: Optional[int] = Form(None),
    image_url: Optional[UploadFile] = File(None),
    size_guide_image: Optional[UploadFile] = File(None),
    is_active: bool = Form(True),
    sort_order: int = Form(0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["categories:create"]))
):
    category_data = CategoryCreate(
        name=name,
        description=description,
        parent_id=parent_id,
        is_active=is_active,
        sort_order=sort_order
    )
    try:
        category = CategoryService.create(db, current_user, category_data, image_url, size_guide_image)
        return category
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/categories/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    parent_id: Optional[int] = Form(None),
    image_url: Optional[UploadFile] = File(None),
    size_guide_image: Optional[UploadFile] = File(None),
    is_active: Optional[bool] = Form(None),
    sort_order: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["categories:update"]))
):
    """
    Update a category - requires categories:update permission.
    
    All fields are optional. Only provided fields will be updated.
    """
    try:
        category_data = CategoryUpdate(
            name=name,
            description=description,
            parent_id=parent_id,
            is_active=is_active,
            sort_order=sort_order
        )
        category = CategoryService.update(db, category_id, category_data, current_user, image_url, size_guide_image)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        return category
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/categories/{category_id}", status_code=status.HTTP_200_OK)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["categories:delete"]))
):
    """
    Delete a category - requires categories:delete permission.
    
    Note: Cannot delete categories that have children or products.
    """
    try:
        success = CategoryService.delete(db, category_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        return {"message": "Category deleted successfully"}
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
