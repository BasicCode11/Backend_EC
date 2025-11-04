from typing import List, Optional, Tuple
from sqlalchemy import select, func, or_, and_, desc, asc
from sqlalchemy.orm import Session, selectinload
from datetime import datetime
from app.models.inventory import Inventory
from app.models.product import Product
from app.models.user import User
from app.schemas.inventory import (
    InventoryCreate,
    InventoryUpdate,
    InventoryAdjustment,
    InventoryReserve,
    InventoryRelease,
    InventoryTransfer,
    InventorySearchParams
)
from app.core.exceptions import ValidationError, NotFoundError
from app.services.audit_log_service import AuditLogService


class InventoryService:
    """Service layer for inventory operations."""

    @staticmethod
    def get_all(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        product_id: Optional[int] = None,
        location: Optional[str] = None
    ) -> Tuple[List[Inventory], int]:
        """Get all inventory records with optional filters"""
        query = select(Inventory).options(
            selectinload(Inventory.product)
        )

        if product_id:
            query = query.where(Inventory.product_id == product_id)
        if location:
            query = query.where(Inventory.location == location)

        count_query = select(func.count()).select_from(query.subquery())
        total = db.execute(count_query).scalar()

        query = query.order_by(desc(Inventory.created_at)).offset(skip).limit(limit)
        inventories = db.execute(query).scalars().all()

        return inventories, total

    @staticmethod
    def search(db: Session, params: InventorySearchParams) -> Tuple[List[Inventory], int]:
        """Search inventory with advanced filters"""
        query = select(Inventory).options(
            selectinload(Inventory.product)
        )

        if params.search:
            search_term = f"%{params.search}%"
            query = query.join(Product).where(
                or_(
                    Product.name.ilike(search_term),
                    Inventory.sku.ilike(search_term),
                    Inventory.batch_number.ilike(search_term),
                    Inventory.location.ilike(search_term)
                )
            )

        if params.product_id:
            query = query.where(Inventory.product_id == params.product_id)
        if params.location:
            query = query.where(Inventory.location.ilike(f"%{params.location}%"))
        if params.min_stock is not None:
            query = query.where(Inventory.stock_quantity >= params.min_stock)
        if params.max_stock is not None:
            query = query.where(Inventory.stock_quantity <= params.max_stock)

        if params.low_stock:
            query = query.where(
                (Inventory.stock_quantity - Inventory.reserved_quantity) <= Inventory.low_stock_threshold
            )

        if params.needs_reorder:
            query = query.where(
                (Inventory.stock_quantity - Inventory.reserved_quantity) <= Inventory.reorder_level
            )

        if params.expired:
            query = query.where(
                and_(
                    Inventory.expiry_date.isnot(None),
                    Inventory.expiry_date < datetime.now()
                )
            )

        count_query = select(func.count()).select_from(query.subquery())
        total = db.execute(count_query).scalar()

        if params.sort_by:
            sort_column = getattr(Inventory, params.sort_by)
            if params.sort_order == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(Inventory.created_at))

        query = query.offset((params.page - 1) * params.limit).limit(params.limit)
        inventories = db.execute(query).scalars().all()

        return inventories, total

    @staticmethod
    def get_by_id(db: Session, inventory_id: int) -> Optional[Inventory]:
        """Get inventory by ID"""
        query = select(Inventory).options(
            selectinload(Inventory.product)
        ).where(Inventory.id == inventory_id)
        return db.execute(query).scalar_one_or_none()
    
    @staticmethod
    def get_by_product_id(db: Session, product_id: int) -> List[Inventory]:
        """Get all inventory records for a specific product"""
        query = select(Inventory).options(
            selectinload(Inventory.product)
        ).where(Inventory.product_id == product_id)
        return db.execute(query).scalars().all()

    @staticmethod
    def get_by_sku(db: Session, sku: str) -> Optional[Inventory]:
        """Get inventory by SKU"""
        query = select(Inventory).options(
            selectinload(Inventory.product)
        ).where(Inventory.sku == sku)
        return db.execute(query).scalar_one_or_none()

    @staticmethod
    def create(
        db: Session,
        inventory_data: InventoryCreate,
        current_user: User
    ) -> Inventory:
        """Create new inventory record"""
        product = db.query(Product).filter(Product.id == inventory_data.product_id).first()
        if not product:
            raise NotFoundError(f"Product with id {inventory_data.product_id} not found")

        if inventory_data.sku:
            existing = InventoryService.get_by_sku(db, inventory_data.sku)
            if existing:
                raise ValidationError(f"Inventory with SKU {inventory_data.sku} already exists")

        inventory = Inventory(**inventory_data.model_dump())
        db.add(inventory)
        db.flush()

        AuditLogService.log_create(
            db=db,
            user_id=current_user.id,
            entity_id=inventory.id,
            entity_type="Inventory",
            entity_uuid=current_user.uuid,
            new_values={
                "product_id": float(inventory.product_id) if inventory.product_id else None,
                "stock_quantity": float(inventory.stock_quantity) if inventory.stock_quantity else None,
                "reserved_quantity": float(inventory.reserved_quantity) if inventory.reserved_quantity else None,
                "low_stock_threshold": float(inventory.low_stock_threshold) if inventory.low_stock_threshold else None,
                "reorder_level": float(inventory.reorder_level) if inventory.reorder_level else None,
                "sku": inventory.sku if inventory.sku else None,
                "batch_number": inventory.batch_number if inventory.batch_number else None,
                "expiry_date": inventory.expiry_date.isoformat() if isinstance(inventory.expiry_date, datetime) else str(inventory.expiry_date) if inventory.expiry_date else None,
                "location": inventory.location if inventory.location else None,
            }
        )

        db.commit()
        db.refresh(inventory)
        return inventory

    @staticmethod
    def update(
        db: Session,
        inventory_id: int,
        inventory_data: InventoryUpdate,
        current_user: User
    ) -> Inventory:
        """Update inventory record"""
        inventory = InventoryService.get_by_id(db, inventory_id)
        if not inventory:
            raise NotFoundError(f"Inventory with id {inventory_id} not found")

        if inventory_data.sku and inventory_data.sku != inventory.sku:
            existing = InventoryService.get_by_sku(db, inventory_data.sku)
            if existing and existing.id != inventory_id:
                raise ValidationError(f"Inventory with SKU {inventory_data.sku} already exists")

        old_data = {
            "product_id": float(inventory.product_id) if inventory.product_id else None,
            "stock_quantity": float(inventory.stock_quantity) if inventory.stock_quantity else None,
            "reserved_quantity": float(inventory.reserved_quantity) if inventory.reserved_quantity else None,
            "low_stock_threshold": float(inventory.low_stock_threshold) if inventory.low_stock_threshold else None,
            "reorder_level": float(inventory.reorder_level) if inventory.reorder_level else None,
            "sku": inventory.sku if inventory.sku else None,
            "batch_number": inventory.batch_number if inventory.batch_number else None,
            "expiry_date": inventory.expiry_date.isoformat() if isinstance(inventory.expiry_date, datetime) else str(inventory.expiry_date) if inventory.expiry_date else None,
            "location": inventory.location if inventory.location else None,
        }

        update_data = inventory_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(inventory, key, value)

        db.flush()
        new_data = {
            "stock_quantity": float(update_data["stock_quantity"]) if update_data.get("stock_quantity") else None,
            "reserved_quantity": float(update_data["reserved_quantity"]) if update_data.get("reserved_quantity") else None,
            "low_stock_threshold": float(update_data["low_stock_threshold"]) if update_data.get("low_stock_threshold") else None,
            "reorder_level": float(update_data["reorder_level"]) if update_data.get("reorder_level") else None,
            "sku": update_data.get("sku"),
            "batch_number": update_data.get("batch_number"),
            "expiry_date": (
                update_data["expiry_date"].isoformat()
                    if isinstance(update_data.get("expiry_date"), datetime)
                    else str(update_data.get("expiry_date")) if update_data.get("expiry_date") else None
            ),
            "location": update_data.get("location"),
        }

        AuditLogService.log_update(
            db=db,
            user_id=current_user.id,
            entity_id=inventory.id,
            entity_type="Inventory",
            entity_uuid=current_user.uuid,
            old_values=old_data,
            new_values=new_data
        )

        db.commit()
        db.refresh(inventory)
        return inventory

    @staticmethod
    def delete(db: Session, inventory_id: int, current_user: User) -> bool:
        """Delete inventory record"""
        inventory = InventoryService.get_by_id(db, inventory_id)
        if not inventory:
            raise NotFoundError(f"Inventory with id {inventory_id} not found")

        if inventory.reserved_quantity > 0:
            raise ValidationError(
                f"Cannot delete inventory with reserved quantity ({inventory.reserved_quantity} units reserved)"
            )
        ldd_data = {
            "product_id": float(inventory.product_id) if inventory.product_id else None,
            "stock_quantity": float(inventory.stock_quantity) if inventory.stock_quantity else None,
            "reserved_quantity": float(inventory.reserved_quantity) if inventory.reserved_quantity else None,
            "low_stock_threshold": float(inventory.low_stock_threshold) if inventory.low_stock_threshold else None,
            "reorder_level": float(inventory.reorder_level) if inventory.reorder_level else None,
            "sku": inventory.sku if inventory.sku else None,
            "batch_number": inventory.batch_number if inventory.batch_number else None,
            "expiry_date": inventory.expiry_date.isoformat() if isinstance(inventory.expiry_date, datetime) else str(inventory.expiry_date) if inventory.expiry_date else None,
            "location": inventory.location if inventory.location else None,
        }
        product_name = inventory.product.name if inventory.product else "Unknown"
        
        db.delete(inventory)
        db.flush()

        AuditLogService.log_delete(
            db=db,
            user_id=current_user.id,
            entity_type="Inventory",
            entity_id=inventory.id,
            entity_uuid=current_user.uuid,
            old_values=ldd_data
        )

        db.commit()
        return True

    @staticmethod
    def adjust_stock(
        db: Session,
        inventory_id: int,
        adjustment: InventoryAdjustment,
        current_user: User
    ) -> Inventory:
        """Adjust inventory stock quantity (add or subtract)"""
        inventory = InventoryService.get_by_id(db, inventory_id)
        if not inventory:
            raise NotFoundError(f"Inventory with id {inventory_id} not found")

        old_quantity = inventory.stock_quantity
        new_quantity = old_quantity + adjustment.quantity

        if new_quantity < 0:
            raise ValidationError(
                f"Insufficient stock. Current: {old_quantity}, Requested adjustment: {adjustment.quantity}"
            )

        if new_quantity < inventory.reserved_quantity:
            raise ValidationError(
                f"Cannot reduce stock below reserved quantity ({inventory.reserved_quantity} units reserved)"
            )

        inventory.stock_quantity = new_quantity
        db.flush()

        action_type = "STOCK_INCREASE" if adjustment.quantity > 0 else "STOCK_DECREASE"
        AuditLogService.log_update(
            db=db,
            user_id=current_user.id,
            entity_id=inventory_id,
            entity_type="Inventory",
            entity_uuid=current_user.uuid,
            old_values= {"stock_quantity": old_quantity},
            new_values= new_quantity
        )

        db.commit()
        db.refresh(inventory)
        return inventory

    @staticmethod
    def reserve_stock(
        db: Session,
        inventory_id: int,
        reserve_data: InventoryReserve,
        current_user: User
    ) -> Inventory:
        """Reserve inventory stock for an order"""
        inventory = InventoryService.get_by_id(db, inventory_id)
        if not inventory:
            raise NotFoundError(f"Inventory with id {inventory_id} not found")

        if inventory.available_quantity < reserve_data.quantity:
            raise ValidationError(
                f"Insufficient available stock. Available: {inventory.available_quantity}, Requested: {reserve_data.quantity}"
            )

        if not inventory.reserve_quantity(reserve_data.quantity):
            raise ValidationError("Failed to reserve stock")

        db.flush()

        order_info = f" for order #{reserve_data.order_id}" if reserve_data.order_id else ""
        AuditLogService.log_create(
            db=db,
            user_id=current_user.id,
            entity_type="Inventory",
            entity_id=inventory.id,
            new_values=f"Reserved {reserve_data.quantity} units{order_info}. Total reserved: {inventory.reserved_quantity}"
        )

        db.commit()
        db.refresh(inventory)
        return inventory

    @staticmethod
    def release_stock(
        db: Session,
        inventory_id: int,
        release_data: InventoryRelease,
        current_user: User
    ) -> Inventory:
        """Release reserved inventory stock"""
        inventory = InventoryService.get_by_id(db, inventory_id)
        if not inventory:
            raise NotFoundError(f"Inventory with id {inventory_id} not found")

        if inventory.reserved_quantity < release_data.quantity:
            raise ValidationError(
                f"Cannot release more than reserved. Reserved: {inventory.reserved_quantity}, Requested: {release_data.quantity}"
            )

        if not inventory.release_quantity(release_data.quantity):
            raise ValidationError("Failed to release stock")

        db.flush()

        order_info = f" from order #{release_data.order_id}" if release_data.order_id else ""
        AuditLogService.log_create(
            db=db,
            user_id=current_user.id,
            entity_type="Inventory",
            entity_id=inventory.id,
            new_values=f"Released {release_data.quantity} units{order_info}. Total reserved: {inventory.reserved_quantity}"
        )

        db.commit()
        db.refresh(inventory)
        return inventory

    @staticmethod
    def fulfill_order(
        db: Session,
        inventory_id: int,
        quantity: int,
        current_user: User,
        order_id: Optional[int] = None
    ) -> Inventory:
        """Fulfill order by reducing both reserved and stock quantities"""
        inventory = InventoryService.get_by_id(db, inventory_id)
        if not inventory:
            raise NotFoundError(f"Inventory with id {inventory_id} not found")

        if inventory.reserved_quantity < quantity:
            raise ValidationError(
                f"Insufficient reserved stock. Reserved: {inventory.reserved_quantity}, Requested: {quantity}"
            )

        inventory.reserved_quantity -= quantity
        inventory.stock_quantity -= quantity
        db.flush()

        order_info = f" for order #{order_id}" if order_id else ""
        AuditLogService.log_create(
            db=db,
            user_id=current_user.id,
            entity_type="ORDER_FULFILLED",
            entity_id=inventory.id,
            new_values=f"Fulfilled {quantity} units{order_info}. Stock: {inventory.stock_quantity}, Reserved: {inventory.reserved_quantity}"
        )

        db.commit()
        db.refresh(inventory)
        return inventory

    @staticmethod
    def transfer_stock(
        db: Session,
        transfer_data: InventoryTransfer,
        current_user: User
    ) -> Tuple[Inventory, Inventory]:
        """Transfer stock between inventory locations"""
        from_inventory = InventoryService.get_by_id(db, transfer_data.from_inventory_id)
        to_inventory = InventoryService.get_by_id(db, transfer_data.to_inventory_id)

        if not from_inventory:
            raise NotFoundError(f"Source inventory with id {transfer_data.from_inventory_id} not found")
        if not to_inventory:
            raise NotFoundError(f"Destination inventory with id {transfer_data.to_inventory_id} not found")

        if from_inventory.product_id != to_inventory.product_id:
            raise ValidationError("Cannot transfer stock between different products")

        if from_inventory.available_quantity < transfer_data.quantity:
            raise ValidationError(
                f"Insufficient available stock in source. Available: {from_inventory.available_quantity}, Requested: {transfer_data.quantity}"
            )

        from_inventory.stock_quantity -= transfer_data.quantity
        to_inventory.stock_quantity += transfer_data.quantity
        db.flush()

        AuditLogService.log_action(
            db=db,
            user_id=current_user.id,
            action="STOCK_TRANSFER",
            resource_type="Inventory",
            resource_id=from_inventory.id,
            details=f"Transferred {transfer_data.quantity} units from inventory #{from_inventory.id} to #{to_inventory.id}. Reason: {transfer_data.reason or 'N/A'}"
        )

        db.commit()
        db.refresh(from_inventory)
        db.refresh(to_inventory)
        return from_inventory, to_inventory

    @staticmethod
    def get_low_stock_items(db: Session) -> List[Inventory]:
        """Get all inventory items with low stock"""
        query = select(Inventory).options(selectinload(Inventory.product)).where(
            (Inventory.stock_quantity - Inventory.reserved_quantity) <= Inventory.low_stock_threshold
        )
        return db.execute(query).scalars().all()
   

    @staticmethod
    def get_reorder_items(db: Session) -> List[Inventory]:
        """Get all inventory items that need reordering"""
        query = select(Inventory).options(
            selectinload(Inventory.product)
        ).where(
            (Inventory.stock_quantity - Inventory.reserved_quantity) <= Inventory.reorder_level
        )
        return db.execute(query).scalars().all()

    @staticmethod
    def get_expired_items(db: Session) -> List[Inventory]:
        """Get all expired inventory items"""
        query = select(Inventory).options(
            selectinload(Inventory.product)
        ).where(
            and_(
                Inventory.expiry_date.isnot(None),
                Inventory.expiry_date < datetime.now()
            )
        )
        return db.execute(query).scalars().all()

    @staticmethod
    def get_statistics(db: Session) -> dict:
        """Get inventory statistics"""
        total_products = db.query(func.count(Inventory.id)).scalar()
        total_stock = db.query(func.sum(Inventory.stock_quantity)).scalar() or 0
        total_reserved = db.query(func.sum(Inventory.reserved_quantity)).scalar() or 0
        total_available = total_stock - total_reserved

        low_stock_count = db.query(func.count(Inventory.id)).filter(
            (Inventory.stock_quantity - Inventory.reserved_quantity) <= Inventory.low_stock_threshold
        ).scalar()

        needs_reorder_count = db.query(func.count(Inventory.id)).filter(
            (Inventory.stock_quantity - Inventory.reserved_quantity) <= Inventory.reorder_level
        ).scalar()

        expired_count = db.query(func.count(Inventory.id)).filter(
            and_(
                Inventory.expiry_date.isnot(None),
                Inventory.expiry_date < datetime.now()
            )
        ).scalar()

        out_of_stock_count = db.query(func.count(Inventory.id)).filter(
            (Inventory.stock_quantity - Inventory.reserved_quantity) <= 0
        ).scalar()

        return {
            "total_products": total_products,
            "total_stock": total_stock,
            "total_reserved": total_reserved,
            "total_available": total_available,
            "low_stock_count": low_stock_count,
            "needs_reorder_count": needs_reorder_count,
            "expired_count": expired_count,
            "out_of_stock_count": out_of_stock_count
        }
