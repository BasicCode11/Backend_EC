from typing import  Optional
from fastapi import APIRouter, Depends, HTTPException, status , Query , UploadFile , File , Form
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.banner import BannerCreate, BannerUpdate , BannerResponse , BannerListResponse
from app.database import get_db
from app.services.banner_service import BannerService
from app.deps.auth import require_permission
router = APIRouter()

@router.get("/banners", response_model=BannerListResponse)
def list_banners(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(20, le=100),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(require_permission(["banners:read"]))
):
    banners, total = BannerService.get_all(db, page, limit, status, search)
    return {
        "banners": banners,
        "total": total,
        "page": page,
        "limit": limit
    }

@router.get("/banners/active", response_model=BannerListResponse)
def list_active_banners(
    db: Session = Depends(get_db),
):
    banners = BannerService.get_active_banners(db)
    return {
        "banners": banners,
        "total": len(banners),
        "page": 1,
        "limit": len(banners)
    }

@router.post("/banners", response_model=BannerResponse, status_code=status.HTTP_201_CREATED)
def create_banner(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    status: Optional[str] = Form(None),
    slug: Optional[str] = Form(None),
    start_date: Optional[str] = Form(None),
    end_date: Optional[str] = Form(None),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["banners:create"]))
):
    banner_create = BannerCreate(
        title=title,
        description=description,
        status=status,
        slug=slug,
        start_date=start_date,
        end_date=end_date
    )
    return BannerService.create(db, banner_create, current_user , image)

@router.get("/banners/{banner_id}", response_model=BannerResponse)
def get_banner(
    banner_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["banners:read"]))
):
    banner = BannerService.get_by_id(db, banner_id)
    if not banner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Banner not found")
    return banner


@router.put("/banners/{banner_id}", response_model=BannerResponse)
def update_banner(
    banner_id: int,
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    status: Optional[str] = Form(None),
    slug: Optional[str] = Form(None),
    start_date: Optional[str] = Form(None),
    end_date: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["banners:update"]))
):
    banner_update = BannerUpdate(
        title=title,
        description=description,
        status=status,
        slug=slug,
        start_date=start_date,
        end_date=end_date
    )
    updated_banner = BannerService.update(db, banner_id, banner_update, current_user, image)
    return updated_banner

@router.delete("/banners/{banner_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_banner(
    banner_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["banners:delete"]))
):
    return BannerService.delete(db, banner_id, current_user)