from typing import List, Optional
from sqlalchemy import select, or_, func
from sqlalchemy.orm import Session, selectinload
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.core.exceptions import ValidationError
from app.models.user import User
from app.services.audit_log_service import AuditLogService
from app.services.file_service import LogoUpload


class CategoryService:
    """Service layer for category operations."""

    @staticmethod
    def get_all(
        db: Session,
        page: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
        parent_id: Optional[int] = None
    ) -> List[Category]:
        """Get all categories with optional filters"""
        query = select(Category).order_by(Category.sort_order, Category.name)

        if is_active is not None:
            query = query.where(Category.is_active == is_active)
        
        if parent_id is not None:
            query = query.where(Category.parent_id == parent_id)

        query = query.offset((page - 1) * limit).limit(limit)
        return db.execute(query).scalars().all()

    @staticmethod
    def get_by_id(db: Session, category_id: int) -> Optional[Category]:
        """Get category by ID"""
        return db.get(Category, category_id)

    @staticmethod
    def get_with_children(db: Session, category_id: int) -> Optional[Category]:
        """Get category with its children loaded"""
        stmt = (
            select(Category)
            .where(Category.id == category_id)
            .options(selectinload(Category.children))
        )
        return db.execute(stmt).scalars().first()

    @staticmethod
    def get_with_parent(db: Session, category_id: int) -> Optional[Category]:
        """Get category with its parent loaded"""
        stmt = (
            select(Category)
            .where(Category.id == category_id)
            .options(selectinload(Category.parent))
        )
        return db.execute(stmt).scalars().first()

    @staticmethod
    def get_root_categories(db: Session) -> List[Category]:
        """Get all root categories (categories without parent)"""
        stmt = select(Category).where(Category.parent_id.is_(None)).order_by(Category.sort_order)
        return db.execute(stmt).scalars().all()

    @staticmethod
    def create(db: Session, current_user: User ,category_data: CategoryCreate , image_url: Optional[str] = None) -> Category:
        """Create a new category"""
        # Validate parent exists if parent_id is provided
        if category_data.parent_id:
            parent = CategoryService.get_by_id(db, category_data.parent_id)
            if not parent:
                raise ValidationError("Parent category not found")
        
        # Check for duplicate name at same level
        existing = CategoryService._get_by_name_and_parent(
            db, 
            category_data.name, 
            category_data.parent_id
        )
        if existing:
            raise ValidationError("Category with this name already exists at this level")
        
        #upload image category 
        picture_url = LogoUpload._save_image(image_url) if image_url else None
        

        db_category = Category(
            name=category_data.name,
            description=category_data.description,
            parent_id=category_data.parent_id,
            image_url=picture_url,
            is_active=category_data.is_active,
            sort_order=category_data.sort_order
        )

        db.add(db_category)
        db.commit()
        db.refresh(db_category)
        
        #audit log data catch 
        AuditLogService.log_create(
            db=db,
            user_id=current_user.id,
            entity_type="Category",
            entity_id=db_category.id,
            new_values={
                "name": db_category.name,
                "description": db_category.description,
                "parent_id": db_category.parent_id,
                "is_active": db_category.is_active,
                "sort_order": db_category.sort_order
            }
        )
        return db_category

    @staticmethod
    def update(db: Session, category_id: int, category_data: CategoryUpdate) -> Optional[Category]:
        """Update a category"""
        db_category = CategoryService.get_by_id(db, category_id)
        if not db_category:
            return None

        # Validate parent exists and prevent circular references
        if category_data.parent_id is not None:
            if category_data.parent_id == category_id:
                raise ValidationError("Category cannot be its own parent")
            
            if category_data.parent_id != 0:
                parent = CategoryService.get_by_id(db, category_data.parent_id)
                if not parent:
                    raise ValidationError("Parent category not found")
                
                # Check if new parent is a descendant of this category
                if CategoryService._is_descendant(db, category_id, category_data.parent_id):
                    raise ValidationError("Cannot set a descendant category as parent")

        # Check for duplicate name if name is being updated
        if category_data.name:
            new_parent_id = category_data.parent_id if category_data.parent_id is not None else db_category.parent_id
            existing = CategoryService._get_by_name_and_parent(
                db, 
                category_data.name, 
                new_parent_id
            )
            if existing and existing.id != category_id:
                raise ValidationError("Category with this name already exists at this level")

        # Update fields
        update_data = category_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_category, field, value)

        db.commit()
        db.refresh(db_category)
        return db_category

    @staticmethod
    def delete(db: Session, category_id: int) -> bool:
        """Delete a category"""
        db_category = CategoryService.get_by_id(db, category_id)
        if not db_category:
            return False

        # Check if category has children
        if db_category.has_children:
            raise ValidationError("Cannot delete category with child categories")

        # Check if category has products
        if len(db_category.products) > 0:
            raise ValidationError("Cannot delete category with products")

        db.delete(db_category)
        db.commit()
        return True



    @staticmethod
    def _get_by_name_and_parent(db: Session, name: str, parent_id: Optional[int]) -> Optional[Category]:
        """Get category by name and parent_id (for duplicate checking)"""
        stmt = select(Category).where(Category.name == name)
        if parent_id:
            stmt = stmt.where(Category.parent_id == parent_id)
        else:
            stmt = stmt.where(Category.parent_id.is_(None))
        return db.execute(stmt).scalars().first()

    @staticmethod
    def _is_descendant(db: Session, ancestor_id: int, potential_descendant_id: int) -> bool:
        """Check if potential_descendant_id is a descendant of ancestor_id"""
        current = CategoryService.get_by_id(db, potential_descendant_id)
        while current and current.parent_id:
            if current.parent_id == ancestor_id:
                return True
            current = CategoryService.get_by_id(db, current.parent_id)
        return False
