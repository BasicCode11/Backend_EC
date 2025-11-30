from typing import List, Optional, Tuple
from sqlalchemy import select, func, or_, and_, desc, asc
from sqlalchemy.orm import Session, selectinload
from app.models.product import Product, ProductStatus
from app.models.product_image import ProductImage
from app.models.product_variant import ProductVariant
from app.models.user import User
from app.models.brand import Brand
from app.models.category import Category
from app.models.inventory import Inventory
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductSearchParams,
    ProductImageCreate,
    ProductVariantCreate
)
from fastapi import HTTPException , status
from app.core.exceptions import ValidationError
from app.services.audit_log_service import AuditLogService
from app.services.file_service import LogoUpload
from app.services.stock_validation_service import StockValidationService

class ProductService:
    """Service layer for product operations."""

    @staticmethod
    def get_all(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
        category_id: Optional[int] = None,
        brand_id: Optional[int] = None,
        featured: Optional[bool] = None,
        search: Optional[str] = None
    ) -> Tuple[List[Product], int]:
        """Get all products with optional filters"""
        query = select(Product).options(
            selectinload(Product.category),
            selectinload(Product.images),
            selectinload(Product.variants).selectinload(ProductVariant.inventory)
        )

        if status:
            query = query.where(Product.status == status)
        if category_id:
            query = query.where(Product.category_id == category_id)
        if brand_id:
            query = query.where(Product.brand_id == brand_id)
        if featured is not None:
            query = query.where(Product.featured == featured)
        if search:
            like_pattern = f"%{search}%"
            query = query.where(
                or_(
                    Product.name.ilike(like_pattern),
                    Product.description.ilike(like_pattern),
                )
            )

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = db.execute(count_query).scalar()

        # Get paginated results
        query = query.order_by(desc(Product.created_at)).offset(skip).limit(limit)
        products = db.execute(query).scalars().all()

        return products, total

    @staticmethod
    def search(db: Session, params: ProductSearchParams) -> Tuple[List[Product], int]:
        """Search products with advanced filters"""
        query = select(Product).options(
            selectinload(Product.category),
            selectinload(Product.images),
            selectinload(Product.inventory),
            selectinload(Product.variants)
        )

        # Text search
        if params.search:
            search_term = f"%{params.search}%"
            query = query.where(
                or_(
                    Product.name.ilike(search_term),
                    Product.description.ilike(search_term),
                    Product.brand.ilike(search_term)
                )
            )

        # Filters
        if params.category_id:
            query = query.where(Product.category_id == params.category_id)
        if params.brand:
            query = query.where(Product.brand.ilike(f"%{params.brand}%"))
        if params.status:
            query = query.where(Product.status == params.status.value)
        if params.featured is not None:
            query = query.where(Product.featured == params.featured)
        if params.min_price is not None:
            query = query.where(Product.price >= params.min_price)
        if params.max_price is not None:
            query = query.where(Product.price <= params.max_price)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = db.execute(count_query).scalar()

        # Sorting
        if params.sort_by:
            sort_column = getattr(Product, params.sort_by)
            if params.sort_order == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(Product.created_at))

        # Pagination
        skip = (params.page - 1) * params.limit
        query = query.offset(skip).limit(params.limit)

        products = db.execute(query).scalars().all()
        return products, total

    @staticmethod
    def get_by_id(db: Session, product_id: int) -> Optional[Product]:
        """Get product by ID"""
        return db.get(Product, product_id)

    @staticmethod
    def get_with_details(db: Session, product_id: int) -> Optional[Product]:
        """Get product with images, variants, and inventory loaded"""
        stmt = (
            select(Product)
            .where(Product.id == product_id)
            .options(
                selectinload(Product.images),
                selectinload(Product.variants).selectinload(ProductVariant.inventory),
            )
        )
        return db.execute(stmt).scalars().first()

    @staticmethod
    def create(db: Session, product_data: ProductCreate , current_user: User , ip_address: str , user_agent: str) -> Product:
        """Create a new product"""
        # Validate category exists
        category = db.get(Category, product_data.category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

        # Validate brand exists
        brand = db.get(Brand, product_data.brand_id)
        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found")

        # Create product
        db_product = Product(
            name=product_data.name,
            description=product_data.description,
            material=product_data.material,
            care_instructions=product_data.care_instructions,
            price=product_data.price,
            compare_price=product_data.compare_price,
            cost_price=product_data.cost_price,
            category_id=product_data.category_id,
            brand_id=product_data.brand_id,
            weight=product_data.weight,
            dimensions=product_data.dimensions,
            featured=product_data.featured,
            status=product_data.status.value
        )

        db.add(db_product)
        db.flush()

        # Create images
        if product_data.images:
            for idx, image_data in enumerate(product_data.images):
                db_image = ProductImage(
                    product_id=db_product.id,
                    image_url=image_data.image_url,
                    image_public_id=image_data.image_public_id,
                    alt_text=image_data.alt_text,
                    sort_order=image_data.sort_order if image_data.sort_order else idx,
                    is_primary=image_data.is_primary
                )
                db.add(db_image)

        # 4️⃣ Create variants
        variant_objects = []
        if product_data.variants:
            for idx, variant_data in enumerate(product_data.variants):
                
                existing_variant = db.execute(
                    select(ProductVariant).where(ProductVariant.sku == variant_data.sku)
                ).scalar_one_or_none()
    
                if existing_variant:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"SKU '{variant_data.sku}' already exists"
                    )
                
                db_variant = ProductVariant(
                    product_id=db_product.id,
                    sku=variant_data.sku,
                    variant_name=variant_data.variant_name,
                    color=variant_data.color,
                    size=variant_data.size,
                    weight=variant_data.weight,
                    additional_price=variant_data.additional_price,
                    sort_order=variant_data.sort_order if variant_data.sort_order else idx
                )
                db.add(db_variant)
                db.flush()  # Ensure db_variant.id exists
                variant_objects.append(db_variant)

        # 5️⃣ Create inventory per variant (must follow variant creation)
        if product_data.inventory and variant_objects:
            # Build SKU → Variant mapping for validation
            variant_sku_map = {v.sku: v for v in variant_objects}

            for inv_data in product_data.inventory:
                sku = inv_data.sku
                if sku not in variant_sku_map:
                    raise HTTPException(status_code=404, detail=f"Inventory SKU '{sku}' does not match any variant")

                variant = variant_sku_map[sku]

                # Validate stock quantity
                variant_stock = getattr(variant, "stock_quantity", 0)
                if variant_stock > inv_data.stock_quantity:
                    raise HTTPException(status_code=404, detail=f"Variant SKU '{sku}' stock ({variant_stock}) cannot exceed inventory stock ({inv_data.stock_quantity})")

                # Create inventory
                db_inventory = Inventory(
                    variant_id=variant.id,
                    stock_quantity=inv_data.stock_quantity,
                    reserved_quantity=inv_data.reserved_quantity,
                    low_stock_threshold=inv_data.low_stock_threshold,
                    reorder_level=inv_data.reorder_level,
                    sku=inv_data.sku,
                    batch_number=inv_data.batch_number,
                    expiry_date=inv_data.expiry_date,
                    location=inv_data.location
                )
                db.add(db_inventory)

        # 6️⃣ Commit transaction
        db.commit()
        db.refresh(db_product)

        db.commit()
        db.refresh(db_product)
        AuditLogService.log_create(
            db=db,
            user_id=current_user.id,
            ip_address=ip_address,
            entity_uuid=current_user.uuid,
            user_agent=user_agent,
            entity_id=db_product.id,
            entity_type="Product",
            new_values={
                "name": db_product.name,
                "description": db_product.description,
                "price": float(db_product.price) if db_product.price else None,
                "compare_price": float(db_product.compare_price) if db_product.compare_price else None,
                "cost_price": float(db_product.cost_price) if db_product.cost_price else None,
                "category_id": db_product.category_id,
                "brand_id": brand.name,
                "weight": float(db_product.weight) if db_product.weight else None,
                "featured": db_product.featured,
                "status": db_product.status
            }
        )
        return db_product

    @staticmethod
    def update(db: Session, product_id: int, product_data: ProductUpdate , current_user: User , ip_address: str , user_agent: str) -> Optional[Product]:
        """Update a product"""
        db_product = ProductService.get_by_id(db, product_id)
        if not db_product:
            return None
        old_values = {
            "name": db_product.name,
            "description": db_product.description,
            "price": float(db_product.price) if db_product.price else None,
            "compare_price": float(db_product.compare_price) if db_product.compare_price else None,
            "cost_price": float(db_product.cost_price) if db_product.cost_price else None,
            "category_id": db_product.category_id,
            "brand_id": db_product.brand_id,
            "weight": float(db_product.weight) if db_product.weight else None,
            "featured": db_product.featured,
            "status": db_product.status
        }
        # Validate category if being updated
        if product_data.category_id:
            category = db.get(Category, product_data.category_id)
            if not category:
                raise HTTPException(status_code=404, detail="Category not found")
        if product_data.brand_id:
            brand = db.get(Brand, product_data.brand_id)
            if not brand:
                raise HTTPException(status_code=404, detail="Brand not found")
        # Update fields
        update_data = product_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == 'status' and value:
                setattr(db_product, field, value.value)
            else:
                setattr(db_product, field, value)

        db.commit()
        db.refresh(db_product)

        new_values = {
            "name": db_product.name,
            "description": db_product.description,
            "price": float(db_product.price) if db_product.price else None,
            "compare_price": float(db_product.compare_price) if db_product.compare_price else None,
            "cost_price": float(db_product.cost_price) if db_product.cost_price else None,
            "category_id": db_product.category_id,
            "brand_id": db_product.brand_id,
            "weight": float(db_product.weight) if db_product.weight else None,
            "featured": db_product.featured,
            "status": db_product.status,
        }
        
        AuditLogService.log_update(
            db=db,
            user_id=current_user.id,
            ip_address=ip_address,
            entity_uuid=current_user.uuid,
            user_agent=user_agent,
            entity_id=db_product.id,
            entity_type="Product",
            old_values=old_values,
            new_values=new_values,
            
        )
        return db_product

    @staticmethod
    def delete(db: Session, product_id: int , current_user: User , ip_address: str , user_agent: str) -> bool:
        """Delete a product"""
        db_product = ProductService.get_by_id(db, product_id)

        if not db_product:
            return False
        
        old_values = {
            "name": db_product.name,
            "description": db_product.description,
            "price": float(db_product.price) if db_product.price else None,
            "compare_price": float(db_product.compare_price) if db_product.compare_price else None,
            "cost_price": float(db_product.cost_price) if db_product.cost_price else None,
            "category_id": db_product.category_id,
            "brand": db_product.brand,
            "weight": float(db_product.weight) if db_product.weight else None,
            "featured": db_product.featured,
            "status": db_product.status
        }
        # Check if product has orders
        if len(db_product.order_items) > 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete product with existing orders")
        
        if len(db_product.variants) > 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot Delete Product whit existing variants")
        
        # Delete product images from filesystem before deleting from database
        for image in db_product.images:
            if image.image_public_id:
                LogoUpload._delete_logo(image.image_public_id)

        db.delete(db_product)
        db.commit()

        
        AuditLogService.log_delete(
            db=db,
            user_id=current_user.id,
            ip_address=ip_address,
            entity_uuid=current_user.uuid,
            user_agent=user_agent,
            old_values=old_values,
            entity_id=db_product.id,
            entity_type="Product"
        )
        return True

    @staticmethod
    def add_image(db: Session, product_id: int, image_data: ProductImageCreate) -> ProductImage:
        """Add an image to a product"""
        product = ProductService.get_by_id(db, product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

        db_image = ProductImage(
            product_id=product_id,
            image_url=image_data.image_url,
            image_public_id=image_data.image_public_id,
            alt_text=image_data.alt_text,
            sort_order=image_data.sort_order,
            is_primary=image_data.is_primary
        )

        # If setting as primary, unset other primary images
        if image_data.is_primary:
            db.query(ProductImage).filter(
                ProductImage.product_id == product_id,
                ProductImage.is_primary == True
            ).update({"is_primary": False})

        db.add(db_image)
        db.commit()
        db.refresh(db_image)
        return db_image

    @staticmethod
    def delete_image(db: Session, image_id: int) -> bool:
        """Delete a product image"""
        db_image = db.get(ProductImage, image_id)
        if not db_image:
            return False
        if db_image.image_public_id:
            LogoUpload._delete_logo(db_image.image_public_id)

        db.delete(db_image)
        db.commit()
        return True

    @staticmethod
    def delete_all_images(db: Session, product_id: int) -> bool:
        """Delete all images for a product"""
        # Get all images for the product
        images = db.query(ProductImage).filter(ProductImage.product_id == product_id).all()
        # Delete images from filesystem and database
        for image in images:
            if image.image_public_id:
                LogoUpload._delete_logo(image.image_public_id)
            db.delete(image)
        db.commit()
        return True
    

    @staticmethod
    def get_featured_products(db: Session, limit: int = 10) -> List[Product]:
        """Get featured products"""
        stmt = (
            select(Product)
            .options(
                selectinload(Product.category),
                selectinload(Product.images),
                selectinload(Product.variants).selectinload(ProductVariant.inventory)
            )
            .where(Product.featured == True)
            .where(Product.status == ProductStatus.ACTIVE.value)
            .order_by(desc(Product.created_at))
            .limit(limit)
        )
        return db.execute(stmt).scalars().all()

    @staticmethod
    def get_by_category(db: Session, category_id: Optional[int] = None, limit: int = 20) -> List[Product]:
        """Get products by category"""
        stmt = (
            select(Product)
            .options(
                selectinload(Product.category),
                selectinload(Product.images),
                selectinload(Product.variants).selectinload(ProductVariant.inventory)
            )
            .where(Product.status == ProductStatus.ACTIVE.value)
            .order_by(desc(Product.created_at))
            .limit(limit)
        )
        if category_id:
            stmt = stmt.where(Product.category_id == category_id)
            
        return db.execute(stmt).scalars().all()

    @staticmethod
    def get_product_count(
        db: Session,
        status: Optional[str] = None,
        category_id: Optional[int] = None
    ) -> int:
        """Count products"""
        query = select(func.count(Product.id))
        
        if status:
            query = query.where(Product.status == status)
        if category_id:
            query = query.where(Product.category_id == category_id)
        
        return db.execute(query).scalar()
