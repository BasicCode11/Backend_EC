from typing import List, Optional
from fastapi import UploadFile, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.orm import Session, selectinload
from app.models.banner import Banner, BannerStatus
from app.models.user import User
from app.schemas.banner import BannerCreate, BannerUpdate 
from app.core.exceptions import ValidationError
from app.services.file_service import LogoUpload
from app.services.audit_log_service import AuditLogService

class BannerService:

    @staticmethod
    def get_all(
        db: Session,
        page: int = 1,
        limit: int = 20,
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> tuple[List[Banner], int]:
        """Get all banners with optional filters"""
        query = select(Banner).options(
            selectinload(Banner.user)
        ).order_by(Banner.created_at.desc())

        if status:
            query = query.where(Banner.status == status)
        
        if search:
            query = query.where(Banner.title.ilike(f"%{search}%"))

        # Get total count before pagination
        count_query = select(func.count()).select_from(query.subquery())
        total = db.execute(count_query).scalar()

        # Apply pagination
        query = query.offset((page - 1) * limit).limit(limit)
        banners = db.execute(query).scalars().all()
        
        return banners, total
    
    @staticmethod
    def get_by_id(db: Session, banner_id: int) -> Optional[Banner]:
        """Get banner by ID"""
        stmt = select(Banner).options(
            selectinload(Banner.user)
        ).where(Banner.id == banner_id)
        return db.execute(stmt).scalar_one_or_none()
    
    @staticmethod
    def create(db: Session, banner_create: BannerCreate, current_user: User, image: UploadFile) -> Banner:
        """Create a new banner"""
        if not image:
            raise ValidationError(detail="Image file is required for banner creation.")
        
    
        if banner_create.start_date and banner_create.end_date:
            if banner_create.start_date >= banner_create.end_date:
                raise ValidationError(detail="Start date must be before end date.")    
        
        cloud  = LogoUpload._save_image(image)
        image_url = cloud["url"]
        image_public_id = cloud["public_id"]
        
        new_banner = Banner(
            created_by=current_user.id,
            title=banner_create.title,
            description=banner_create.description,
            status=banner_create.status,
            slug=banner_create.slug,
            start_date=banner_create.start_date,
            end_date=banner_create.end_date,
            image=image_url,
            image_public_id=image_public_id,
        )
        
        db.add(new_banner)
        db.commit()
        db.refresh(new_banner)
        
        # Log audit
        AuditLogService.log_create(
            db=db,
            user_id=current_user.id,
            entity_id=new_banner.id,
            entity_type="banner",
            new_values={
                "title": new_banner.title,
                "description": new_banner.description,
                "status": new_banner.status,
                "slug": new_banner.slug,
                "start_date": new_banner.start_date,
                "end_date": new_banner.end_date,
            }
        )
        return new_banner
    

    @staticmethod
    def update(db: Session, banner_id: int, banner_update: BannerUpdate, current_user: User, image: Optional[UploadFile] = None) -> Banner:
        """Update an existing banner"""
        banner = BannerService.get_by_id(db, banner_id)
        if not banner:
            raise HTTPException(status_code=404, detail="Banner not found")
        
        old_values = {
            "title": banner.title,
            "description": banner.description,
            "status": banner.status,
            "slug": banner.slug,
            "start_date": banner.start_date if banner.start_date else None,
            "end_date": banner.end_date if banner.end_date else None,
        }
        
        if image:
            # Delete old image
            LogoUpload._delete_logo(banner.image_public_id)
            # Upload new image
            cloud = LogoUpload._save_image(image)
            banner.image = cloud["url"]
            banner.image_public_id = cloud["public_id"]
        
        for field, value in banner_update.dict(exclude_unset=True).items():
            setattr(banner, field, value)
        
        db.commit()
        db.refresh(banner)
        
        # Log audit
        new_values = {
            "title": banner.title,
            "description": banner.description,
            "status": banner.status,
            "slug": banner.slug,
            "start_date": banner.start_date,
            "end_date": banner.end_date,
        }
        AuditLogService.log_update(
            db=db,
            user_id=current_user.id,
            entity_id=banner.id,
            entity_type="banner",
            old_values=old_values,
            new_values=new_values
        )
        
        return banner
    
    @staticmethod
    def delete(db: Session, banner_id: int, current_user: User) -> None:
        """Delete a banner"""
        banner = BannerService.get_by_id(db, banner_id)
        if not banner:
            raise HTTPException(status_code=404, detail="Banner not found")
        
        # Delete image
        LogoUpload._delete_logo(banner.image_public_id)
        
        db.delete(banner)
        db.commit()
        
        # Log audit
        AuditLogService.log_delete(
            db=db,
            user_id=current_user.id,
            entity_id=banner.id,
            entity_type="banner",
            old_values={
                "title": banner.title,
                "description": banner.description,
                "status": banner.status,
                "slug": banner.slug,
                "start_date": banner.start_date,
                "end_date": banner.end_date,
            }
        )
        return {"message": "Banner deleted successfully"}
    
    @staticmethod
    def get_active_banners(db: Session) -> List[Banner]:
        """Get all active banners"""
        stmt = select(Banner).where(Banner.status == BannerStatus.OPEN)
        return db.execute(stmt).scalars().all()