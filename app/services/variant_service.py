from typing import List, Optional, Tuple
from sqlalchemy import select, func, or_, and_, desc, asc
from sqlalchemy.orm import Session, selectinload
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.inventory import Inventory
from app.models.user import User
from app.schemas.variant import (
    VariantCreateWithInventory,
    VariantUpdateWithInventory,
    VariantSearchParams
)
from fastapi import HTTPException , status
from app.core.exceptions import ValidationError, NotFoundError
from app.services.audit_log_service import AuditLogService


class VariantService:
    """Service layer for product variant operations."""

    @staticmethod
    def get_all(
        db: Session,
        params: VariantSearchParams
    ) -> Tuple[List[ProductVariant], int]:

        query = select(ProductVariant).options(
            selectinload(ProductVariant.product),
            selectinload(ProductVariant.inventory)
        )

        # Filter by product_id
        if params.product_id:
            query = query.where(ProductVariant.product_id == params.product_id)

        # Search by variant name
        if params.search:
            like_pattern = f"%{params.search}%"
            query = query.where(ProductVariant.variant_name.ilike(like_pattern))

        # Filter by low stock
        if params.low_stock is not None:
            if params.low_stock:
                # Join with inventory to filter low stock variants
                query = query.join(ProductVariant.inventory).where(
                    Inventory.stock_quantity - Inventory.reserved_quantity <= Inventory.low_stock_threshold
                )

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = db.execute(count_query).scalar()

        # Sorting
        sort_column = getattr(ProductVariant, params.sort_by)
        if params.sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))

        # Pagination
        skip = (params.page - 1) * params.limit
        query = query.offset(skip).limit(params.limit)

        variants = db.execute(query).scalars().all()
        return variants, total

    @staticmethod
    def get_by_id(db: Session, variant_id: int) -> Optional[ProductVariant]:
        """Get variant by ID with inventory loaded"""
        stmt = (
            select(ProductVariant)
            .where(ProductVariant.id == variant_id)
            .options(
                selectinload(ProductVariant.product),
                selectinload(ProductVariant.inventory)
            )
        )
        return db.execute(stmt).scalars().first()

    @staticmethod
    def create(
        db: Session,
        variant_data: VariantCreateWithInventory,
        current_user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> ProductVariant:
        """
        Create a new variant with inventory.
        
        Steps:
        1. Validate product exists
        2. Check SKU uniqueness
        3. Create variant
        4. Create inventory records
        """
        # 1. Validate product exists
        product = db.get(Product, variant_data.product_id)
        if not product:
            raise HTTPException(status_code=404, detail=f"Product with ID {product.id} not found")
        
        # 2. Check SKU uniqueness if provided
        if variant_data.sku:
            existing_variant = db.query(ProductVariant).filter(
                ProductVariant.sku == variant_data.sku
            ).first()
            if existing_variant:
                raise HTTPException(status_code=400, detail=f"SKU '{variant_data.sku}' already exists")

        # 3. Create variant
        db_variant = ProductVariant(
            product_id=variant_data.product_id,
            sku=variant_data.sku,
            variant_name=variant_data.variant_name,
            color=variant_data.color,
            size=variant_data.size,
            weight=variant_data.weight,
            additional_price=variant_data.additional_price,
            sort_order=variant_data.sort_order
        )

        db.add(db_variant)
        db.flush()  # Get variant ID

        # 4. Create inventory records
        for inv_data in variant_data.inventory:
            db_inventory = Inventory(
                variant_id=db_variant.id,
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

        db.commit()
        db.refresh(db_variant)

        # Audit log
        AuditLogService.log_create(
            db=db,
            user_id=current_user.id,
            ip_address=ip_address,
            entity_uuid=current_user.uuid,
            user_agent=user_agent,
            entity_id=db_variant.id,
            entity_type="ProductVariant",
            new_values={
                "variant_name": db_variant.variant_name,
                "sku": db_variant.sku,
                "product_id": db_variant.product_id,
                "color": db_variant.color,
                "size": db_variant.size,
                "weight": db_variant.weight,
                "additional_price": float(db_variant.additional_price) if db_variant.additional_price else None,
                "inventory_count": len(variant_data.inventory)
            }
        )

        return db_variant

    @staticmethod
    def update(
        db: Session,
        variant_id: int,
        variant_data: VariantUpdateWithInventory,
        current_user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[ProductVariant]:
        """
        Update a variant and its inventory.
        
        Steps:
        1. Get existing variant
        2. Update variant fields
        3. Update or create inventory records
        """
        # 1. Get existing variant
        db_variant = VariantService.get_by_id(db, variant_id)
        if not db_variant:
            return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found")

        # Store old values for audit log
        old_values = {
            "variant_name": db_variant.variant_name,
            "sku": db_variant.sku,
            "color": db_variant.color,
            "size": db_variant.size,
            "weight": db_variant.weight,
            "additional_price": float(db_variant.additional_price) if db_variant.additional_price else None,
            "sort_order": db_variant.sort_order
        }

        # 2. Update variant fields
        update_data = variant_data.model_dump(exclude_unset=True, exclude={'inventory'})
        
        # Check SKU uniqueness if being updated
        if 'sku' in update_data and update_data['sku'] != db_variant.sku:
            existing_variant = db.query(ProductVariant).filter(
                ProductVariant.sku == update_data['sku'],
                ProductVariant.id != variant_id
            ).first()
            if existing_variant:
                return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"SKU '{update_data['sku']}' already exists")

        for field, value in update_data.items():
            setattr(db_variant, field, value)

        # 3. Update inventory records if provided
        if variant_data.inventory is not None:
            # For simplicity, we'll update existing inventory or create new ones
            # If there are existing inventory records, update the first one
            # If more inventory data is provided than exists, create new ones
            
            existing_inventory = list(db_variant.inventory)
            
            for idx, inv_data in enumerate(variant_data.inventory):
                inv_update = inv_data.model_dump(exclude_unset=True, exclude_none=True)
                
                if idx < len(existing_inventory):
                    # Update existing inventory
                    for field, value in inv_update.items():
                        setattr(existing_inventory[idx], field, value)
                else:
                    # Create new inventory record
                    db_inventory = Inventory(
                        variant_id=db_variant.id,
                        **inv_update
                    )
                    db.add(db_inventory)

        db.commit()
        db.refresh(db_variant)

        # Audit log
        new_values = {
            "variant_name": db_variant.variant_name,
            "sku": db_variant.sku,
            "color": db_variant.color,
            "size": db_variant.size,
            "weight": db_variant.weight,
            "additional_price": float(db_variant.additional_price) if db_variant.additional_price else None,
            "sort_order": db_variant.sort_order
        }

        AuditLogService.log_update(
            db=db,
            user_id=current_user.id,
            ip_address=ip_address,
            entity_uuid=current_user.uuid,
            user_agent=user_agent,
            entity_id=db_variant.id,
            entity_type="ProductVariant",
            old_values=old_values,
            new_values=new_values
        )

        return db_variant

    @staticmethod
    def delete(
        db: Session,
        variant_id: int,
        current_user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """
        Delete a variant and its inventory (cascade).
        
        The inventory will be automatically deleted due to CASCADE relationship.
        """
        db_variant = VariantService.get_by_id(db, variant_id)
        if not db_variant:
            return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found")

        # Check if variant is used in orders
        if len(db_variant.order_items) > 0:
            return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete variant with existing orders")

        # Check if variant is in carts
        if len(db_variant.cart_items) > 0:
            return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete variant currently in shopping carts")

        # Store values for audit log
        old_values = {
            "variant_name": db_variant.variant_name,
            "sku": db_variant.sku,
            "product_id": db_variant.product_id,
            "color": db_variant.color,
            "size": db_variant.size,
            "weight": db_variant.weight,
            "additional_price": float(db_variant.additional_price) if db_variant.additional_price else None,
            "inventory_count": len(db_variant.inventory)
        }

        # Delete variant (inventory will cascade delete automatically)
        db.delete(db_variant)
        db.commit()

        # Audit log
        AuditLogService.log_delete(
            db=db,
            user_id=current_user.id,
            ip_address=ip_address,
            entity_uuid=current_user.uuid,
            user_agent=user_agent,
            entity_id=variant_id,
            entity_type="ProductVariant",
            old_values=old_values
        )

        return True

    @staticmethod
    def get_variant_count(db: Session, product_id: Optional[int] = None) -> int:
        """Count variants with optional product filter"""
        query = select(func.count(ProductVariant.id))
        
        if product_id:
            query = query.where(ProductVariant.product_id == product_id)
        
        return db.execute(query).scalar()
