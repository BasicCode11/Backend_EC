from typing import List, Optional
from fastapi import UploadFile , HTTPException , status
from sqlalchemy import select, func
from sqlalchemy.orm import Session, selectinload
from app.models.brand import Brand, BrandStatus
from app.models.user import User
from app.schemas.brand import BrandCreate, BrandUpdate
from app.core.exceptions import ValidationError
from app.services.audit_log_service import AuditLogService
from app.services.file_service import LogoUpload


class BrandService:
    """Service layer for brand operations."""

    @staticmethod
    def get_all(
        db: Session,
        page: int = 1,
        limit: int = 20,
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> tuple[List[Brand], int]:
        """Get all brands with optional filters"""
        query = select(Brand).options(
            selectinload(Brand.user)
        ).order_by(Brand.name)

        if status:
            query = query.where(Brand.status == status)
        
        if search:
            query = query.where(Brand.name.ilike(f"%{search}%"))

        # Get total count before pagination
        count_query = select(func.count()).select_from(query.subquery())
        total = db.execute(count_query).scalar()

        # Apply pagination
        query = query.offset((page - 1) * limit).limit(limit)
        brands = db.execute(query).scalars().all()
        
        return brands, total

    @staticmethod
    def get_by_id(db: Session, brand_id: int) -> Optional[Brand]:
        """Get brand by ID"""
        stmt = select(Brand).options(
            selectinload(Brand.user)
        ).where(Brand.id == brand_id)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_by_name(db: Session, name: str) -> Optional[Brand]:
        """Get brand by name"""
        stmt = select(Brand).where(Brand.name == name)
        return db.execute(stmt).scalars().first()

    @staticmethod
    def create(
        db: Session,
        current_user: User,
        brand_data: BrandCreate,
        logo: UploadFile
    ) -> Brand:
        """Create a new brand"""
        # Check for duplicate name
        existing = BrandService.get_by_name(db, brand_data.name)
        if existing:
            raise HTTPException(status_code=400, detail=f"Brand with name '{brand_data.name}' already exists")

        # Upload logo to Cloudinary (required)
        if not logo:
            raise HTTPException(status_code=400, detail="Logo is required")

        cloud = LogoUpload._save_image(logo)
        logo_url = cloud["url"]
        logo_public_id = cloud["public_id"]

        # Create brand
        db_brand = Brand(
            name=brand_data.name,
            description=brand_data.description,
            logo=logo_url,
            logo_public_id=logo_public_id,
            status=brand_data.status,
            created_by=current_user.id
        )

        db.add(db_brand)
        db.commit()
        db.refresh(db_brand)

        # Audit log
        AuditLogService.log_create(
            db=db,
            user_id=current_user.id,
            entity_type="Brand",
            entity_id=db_brand.id,
            new_values={
                "name": db_brand.name,
                "description": db_brand.description,
                "status": db_brand.status
            }
        )

        return db_brand

    @staticmethod
    def update(
        db: Session,
        brand_id: int,
        brand_data: BrandUpdate,
        current_user: User,
        logo: Optional[UploadFile] = None
    ) -> Optional[Brand]:
        """Update a brand"""
        db_brand = BrandService.get_by_id(db, brand_id)
        if not db_brand:
            return None

        # Store old values for audit log
        old_values = {
            "name": db_brand.name,
            "description": db_brand.description,
            "logo": db_brand.logo,
            "status": db_brand.status
        }

        # Handle logo upload
        if logo:
            # Delete old logo
            if db_brand.logo_public_id:
                LogoUpload._delete_logo(db_brand.logo_public_id)
            
            # Upload new logo
            cloud = LogoUpload._save_image(logo)
            db_brand.logo = cloud["url"]
            db_brand.logo_public_id = cloud["public_id"]

        # Check for duplicate name if name is being updated
        if brand_data.name and brand_data.name != db_brand.name:
            existing = BrandService.get_by_name(db, brand_data.name)
            if existing:
                raise ValidationError(f"Brand with name '{brand_data.name}' already exists")

        # Update fields
        update_data = brand_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_brand, field, value)

        db.commit()
        db.refresh(db_brand)

        # Log audit changes
        new_values = {
            "name": db_brand.name,
            "description": db_brand.description,
            "logo": db_brand.logo,
            "status": db_brand.status
        }
        
        AuditLogService.log_update(
            db=db,
            user_id=current_user.id,
            entity_type="Brand",
            entity_id=db_brand.id,
            old_values=old_values,
            new_values=new_values
        )

        return db_brand

    @staticmethod
    def delete(db: Session, brand_id: int) -> bool:
        """Delete a brand"""
        db_brand = BrandService.get_by_id(db, brand_id)
        if not db_brand:
            return False

        # Check if brand has products
        if len(db_brand.products) > 0:
            raise ValidationError(
                f"Cannot delete brand with {len(db_brand.products)} associated product(s)"
            )

        # Delete logo from Cloudinary
        if db_brand.logo_public_id:
            LogoUpload._delete_logo(db_brand.logo_public_id)

        db.delete(db_brand)
        db.commit()
        return True

    @staticmethod
    def count_products(db: Session, brand_id: int) -> int:
        """Count products for a brand"""
        stmt = select(func.count()).select_from(Brand).where(Brand.id == brand_id)
        brand = BrandService.get_by_id(db, brand_id)
        if not brand:
            return 0
        return len(brand.products)
