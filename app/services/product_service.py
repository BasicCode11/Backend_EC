from typing import List, Optional, Tuple
from sqlalchemy import select, func, or_, and_, desc, asc
from sqlalchemy.orm import Session, selectinload
from app.models.product import Product, ProductStatus
from app.models.product_image import ProductImage
from app.models.product_variant import ProductVariant
from app.models.user import User
from app.models.category import Category
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductSearchParams,
    ProductImageCreate,
    ProductVariantCreate
)
from app.core.exceptions import ValidationError
from app.services.audit_log_service import AuditLogService

class ProductService:
    """Service layer for product operations."""

    @staticmethod
    def get_all(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
        category_id: Optional[int] = None,
        featured: Optional[bool] = None
    ) -> Tuple[List[Product], int]:
        """Get all products with optional filters"""
        query = select(Product)

        if status:
            query = query.where(Product.status == status)
        if category_id:
            query = query.where(Product.category_id == category_id)
        if featured is not None:
            query = query.where(Product.featured == featured)

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
        query = select(Product)

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
        """Get product with images and variants loaded"""
        stmt = (
            select(Product)
            .where(Product.id == product_id)
            .options(
                selectinload(Product.images),
                selectinload(Product.variants)
            )
        )
        return db.execute(stmt).scalars().first()

    @staticmethod
    def create(db: Session, product_data: ProductCreate , current_user: User , ip_address: str , user_agent: str) -> Product:
        """Create a new product"""
        # Validate category exists
        category = db.get(Category, product_data.category_id)
        if not category:
            raise ValidationError("Category not found")

        # Create product
        db_product = Product(
            name=product_data.name,
            description=product_data.description,
            price=product_data.price,
            compare_price=product_data.compare_price,
            cost_price=product_data.cost_price,
            category_id=product_data.category_id,
            brand=product_data.brand,
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
                    alt_text=image_data.alt_text,
                    sort_order=image_data.sort_order if image_data.sort_order else idx,
                    is_primary=image_data.is_primary
                )
                db.add(db_image)

        # Create variants
        if product_data.variants:
            for idx, variant_data in enumerate(product_data.variants):
                db_variant = ProductVariant(
                    product_id=db_product.id,
                    sku=variant_data.sku,
                    variant_name=variant_data.variant_name,
                    attributes=variant_data.attributes,
                    price=variant_data.price,
                    stock_quantity=variant_data.stock_quantity,
                    image_url=variant_data.image_url,
                    sort_order=variant_data.sort_order if variant_data.sort_order else idx
                )
                db.add(db_variant)

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
                "brand": db_product.brand,
                "weight": float(db_product.weight) if db_product.weight else None,
                "featured": db_product.featured,
                "status": db_product.status
            }
        )
        return db_product

    @staticmethod
    def update(db: Session, product_id: int, product_data: ProductUpdate) -> Optional[Product]:
        """Update a product"""
        db_product = ProductService.get_by_id(db, product_id)
        if not db_product:
            return None

        # Validate category if being updated
        if product_data.category_id:
            category = db.get(Category, product_data.category_id)
            if not category:
                raise ValidationError("Category not found")

        # Update fields
        update_data = product_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == 'status' and value:
                setattr(db_product, field, value.value)
            else:
                setattr(db_product, field, value)

        db.commit()
        db.refresh(db_product)
        return db_product

    @staticmethod
    def delete(db: Session, product_id: int) -> bool:
        """Delete a product"""
        db_product = ProductService.get_by_id(db, product_id)
        if not db_product:
            return False

        # Check if product has orders
        if len(db_product.order_items) > 0:
            raise ValidationError("Cannot delete product with existing orders")

        db.delete(db_product)
        db.commit()
        return True

    @staticmethod
    def add_image(db: Session, product_id: int, image_data: ProductImageCreate) -> ProductImage:
        """Add an image to a product"""
        product = ProductService.get_by_id(db, product_id)
        if not product:
            raise ValidationError("Product not found")

        db_image = ProductImage(
            product_id=product_id,
            image_url=image_data.image_url,
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

        db.delete(db_image)
        db.commit()
        return True

    @staticmethod
    def add_variant(db: Session, product_id: int, variant_data: ProductVariantCreate) -> ProductVariant:
        """Add a variant to a product"""
        product = ProductService.get_by_id(db, product_id)
        if not product:
            raise ValidationError("Product not found")

        db_variant = ProductVariant(
            product_id=product_id,
            sku=variant_data.sku,
            variant_name=variant_data.variant_name,
            attributes=variant_data.attributes,
            price=variant_data.price,
            stock_quantity=variant_data.stock_quantity,
            image_url=variant_data.image_url,
            sort_order=variant_data.sort_order
        )

        db.add(db_variant)
        db.commit()
        db.refresh(db_variant)
        return db_variant

    @staticmethod
    def update_variant(db: Session, variant_id: int, variant_data: ProductVariantCreate) -> Optional[ProductVariant]:
        """Update a product variant"""
        db_variant = db.get(ProductVariant, variant_id)
        if not db_variant:
            return None

        update_data = variant_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_variant, field, value)

        db.commit()
        db.refresh(db_variant)
        return db_variant

    @staticmethod
    def delete_variant(db: Session, variant_id: int) -> bool:
        """Delete a product variant"""
        db_variant = db.get(ProductVariant, variant_id)
        if not db_variant:
            return False

        db.delete(db_variant)
        db.commit()
        return True

    @staticmethod
    def get_featured_products(db: Session, limit: int = 10) -> List[Product]:
        """Get featured products"""
        stmt = (
            select(Product)
            .where(Product.featured == True)
            .where(Product.status == ProductStatus.ACTIVE.value)
            .order_by(desc(Product.created_at))
            .limit(limit)
        )
        return db.execute(stmt).scalars().all()

    @staticmethod
    def get_by_category(db: Session, category_id: int, limit: int = 20) -> List[Product]:
        """Get products by category"""
        stmt = (
            select(Product)
            .where(Product.category_id == category_id)
            .where(Product.status == ProductStatus.ACTIVE.value)
            .order_by(desc(Product.created_at))
            .limit(limit)
        )
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
