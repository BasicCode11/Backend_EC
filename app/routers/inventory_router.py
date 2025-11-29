from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, status, Query, Request, Body
from sqlalchemy.orm import Session
from math import ceil
from app.database import get_db
from app.models.user import User
from app.schemas.inventory import (
    InventoryCreate,
    InventoryUpdate,
    InventoryResponse,
    InventoryWithVariant,
    InventoryListResponse,
    InventoryAdjustment,
    InventoryReserve,
    InventoryRelease,
    InventoryTransfer,
    InventorySearchParams,
    InventoryStatsResponse
)
from app.services.inventory_service import InventoryService
from app.services.inventory_alert_service import InventoryAlertService
from app.services.telegram_service import TelegramService
from app.deps.auth import get_current_active_user, require_permission

router = APIRouter()


def transform_inventory_response(inventory) -> InventoryWithVariant:
    """Helper function to transform inventory with computed properties"""
    from app.schemas.inventory import VariantSimple
    
    variant_obj = None
    if inventory.variant:
        variant_obj = VariantSimple(
            id=inventory.variant.id,
            variant_name=inventory.variant.variant_name,
            sku=inventory.variant.sku,
            additional_price=inventory.variant.additional_price,
            color=inventory.variant.color,
            size=inventory.variant.size
        )
    
    return InventoryWithVariant(
        id=inventory.id,
        variant_id=inventory.variant_id,
        stock_quantity=inventory.stock_quantity,
        reserved_quantity=inventory.reserved_quantity,
        low_stock_threshold=inventory.low_stock_threshold,
        reorder_level=inventory.reorder_level,
        sku=inventory.sku,
        batch_number=inventory.batch_number,
        expiry_date=inventory.expiry_date,
        location=inventory.location,
        available_quantity=inventory.available_quantity,
        is_low_stock=inventory.is_low_stock,
        needs_reorder=inventory.needs_reorder,
        is_expired=inventory.is_expired,
        created_at=inventory.created_at,
        updated_at=inventory.updated_at,
        variant=variant_obj,
    )


@router.get("/inventory", response_model=InventoryListResponse)
def get_all_inventory(
    variant_id: Optional[int] = Query(None, description="Filter by variant ID"),
    search: Optional[str] = Query(None, description="Search by variant name or SKU or batch number"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
    current_user: User = Depends(require_permission(["inventory:read"]))
):
    """Get all inventory records with pagination"""
    skip = (page - 1) * limit

    inventories, total = InventoryService.get_all(
        db=db,
        skip=skip,
        limit=limit,
        variant_id=variant_id,
        search=search
    )
    
    items = [transform_inventory_response(inv) for inv in inventories]
    
    return InventoryListResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        pages=ceil(total / limit) if total > 0 else 0
    )


@router.post("/inventory/search", response_model=InventoryListResponse)
def search_inventory(
    params: InventorySearchParams,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
    current_user: User = Depends(require_permission(["inventory:read"]))
):
    """Search inventory with advanced filters"""
    inventories, total = InventoryService.search(db=db, params=params)
    
    items = [transform_inventory_response(inv) for inv in inventories]
    
    return InventoryListResponse(
        items=items,
        total=total,
        page=params.page,
        limit=params.limit,
        pages=ceil(total / params.limit) if total > 0 else 0
    )


@router.get("/inventory/statistics", response_model=InventoryStatsResponse)
def get_inventory_statistics(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
    current_user: User = Depends(require_permission(["inventory:read"]))
):
    """Get inventory statistics"""
    stats = InventoryService.get_statistics(db=db)
    return InventoryStatsResponse(**stats)


@router.get("/inventory/low-stock", response_model=List[InventoryWithVariant])
def get_low_stock_items(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
    current_user: User = Depends(require_permission(["inventory:read"]))
):
    """Get all inventory items with low stock"""
    inventories = InventoryService.get_low_stock_items(db=db)
    return [transform_inventory_response(inv) for inv in inventories]


@router.get("/inventory/reorder", response_model=List[InventoryWithVariant])
def get_reorder_items(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
    current_user: User = Depends(require_permission(["inventory:read"]))
):
    """Get all inventory items that need reordering"""
    inventories = InventoryService.get_reorder_items(db=db)
    return [transform_inventory_response(inv) for inv in inventories]


@router.get("/inventory/expired", response_model=List[InventoryWithVariant])
def get_expired_items(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
    current_user: User = Depends(require_permission(["inventory:read"]))
):
    """Get all expired inventory items"""
    inventories = InventoryService.get_expired_items(db=db)
    return [transform_inventory_response(inv) for inv in inventories]


@router.get("/inventory/{inventory_id}", response_model=InventoryWithVariant)
def get_inventory(
    inventory_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
    current_user: User = Depends(require_permission(["inventory:read"]))
):
    """Get inventory by ID"""
    inventory = InventoryService.get_by_id(db=db, inventory_id=inventory_id)
    return transform_inventory_response(inventory)


@router.get("/inventory/product/{product_id}", response_model=List[InventoryWithVariant])
def get_inventory_by_product(
    product_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
    current_user: User = Depends(require_permission(["inventory:read"]))
):
    """Get all inventory records for a specific product"""
    inventories = InventoryService.get_by_product_id(db=db, product_id=product_id)
    return [transform_inventory_response(inv) for inv in inventories]


@router.get("/inventory/sku/{sku}", response_model=InventoryWithVariant)
def get_inventory_by_sku(
    sku: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
    current_user: User = Depends(require_permission(["inventory:read"]))
):
    """Get inventory by SKU"""
    inventory = InventoryService.get_by_sku(db=db, sku=sku)
    return transform_inventory_response(inventory)


@router.post(
    "/inventory",
    response_model=InventoryWithVariant,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(["inventory:create"]))]
)
def create_inventory(
    inventory: InventoryCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
    current_user: User = Depends(require_permission(["inventory:create"])),
):
    """Create new inventory record (requires create:inventory permission)"""
    new_inventory = InventoryService.create(
        db=db,
        inventory_data=inventory,
        current_user=current_user
    )
    return transform_inventory_response(new_inventory)


@router.put(
    "/inventory/{inventory_id}",
    response_model=InventoryWithVariant,
    dependencies=[Depends(require_permission(["inventory:update"]))]
)
def update_inventory(
    inventory_id: int,
    inventory: InventoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update inventory record (requires update:inventory permission)"""
    updated_inventory = InventoryService.update(
        db=db,
        inventory_id=inventory_id,
        inventory_data=inventory,
        current_user=current_user
    )
    return transform_inventory_response(updated_inventory)


@router.delete(
    "/inventory/{inventory_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission(["inventory:delete"]))]
)
def delete_inventory(
    inventory_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete inventory record (requires delete:inventory permission)"""
    InventoryService.delete(
        db=db,
        inventory_id=inventory_id,
        current_user=current_user
    )
    return None


@router.post(
    "/inventory/{inventory_id}/adjust",
    response_model=InventoryWithVariant,
    dependencies=[Depends(require_permission(["inventory:adjust"]))]
)
def adjust_inventory_stock(
    inventory_id: int,
    adjustment: InventoryAdjustment,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Adjust inventory stock quantity (add or subtract)
    Requires adjust:inventory permission
    
    - **quantity**: Positive to add stock, negative to reduce stock
    - **reason**: Optional reason for the adjustment
    """
    adjusted_inventory = InventoryService.adjust_stock(
        db=db,
        inventory_id=inventory_id,
        adjustment=adjustment,
        current_user=current_user
    )
    return transform_inventory_response(adjusted_inventory)


@router.post(
    "/inventory/{inventory_id}/reserve",
    response_model=InventoryWithVariant,
)
def reserve_inventory_stock(
    inventory_id: int,
    reserve_data: InventoryReserve,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Reserve inventory stock for an order
    Requires reserve:inventory permission
    
    - **quantity**: Quantity to reserve
    - **order_id**: Optional order ID for tracking
    """
    reserved_inventory = InventoryService.reserve_stock(
        db=db,
        inventory_id=inventory_id,
        reserve_data=reserve_data,
        current_user=current_user
    )
    return transform_inventory_response(reserved_inventory)


@router.post(
    "/inventory/{inventory_id}/release",
    response_model=InventoryWithVariant
)
def release_inventory_stock(
    inventory_id: int,
    release_data: InventoryRelease,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Release reserved inventory stock
    Requires release:inventory permission
    
    - **quantity**: Quantity to release
    - **order_id**: Optional order ID for tracking
    """
    released_inventory = InventoryService.release_stock(
        db=db,
        inventory_id=inventory_id,
        release_data=release_data,
        current_user=current_user
    )
    return transform_inventory_response(released_inventory)


@router.post(
    "/inventory/{inventory_id}/fulfill",
    response_model=InventoryWithVariant
)
def fulfill_order_inventory(
    inventory_id: int,
    quantity: int = Query(..., ge=1, description="Quantity to fulfill"),
    order_id: Optional[int] = Query(None, description="Order ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Fulfill order by reducing both reserved and stock quantities
    Requires fulfill:inventory permission
    
    - **quantity**: Quantity to fulfill
    - **order_id**: Optional order ID for tracking
    """
    fulfilled_inventory = InventoryService.fulfill_order(
        db=db,
        inventory_id=inventory_id,
        quantity=quantity,
        current_user=current_user,
        order_id=order_id
    )
    return transform_inventory_response(fulfilled_inventory)


@router.post(
    "/inventory/transfer",
    response_model=List[InventoryWithVariant]
)
def transfer_inventory_stock(
    transfer_data: InventoryTransfer,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Transfer stock between inventory locations
    Requires transfer:inventory permission
    
    - **from_inventory_id**: Source inventory ID
    - **to_inventory_id**: Destination inventory ID
    - **quantity**: Quantity to transfer
    - **reason**: Optional reason for the transfer
    """
    from_inv, to_inv = InventoryService.transfer_stock(
        db=db,
        transfer_data=transfer_data,
        current_user=current_user
    )
    return [
        transform_inventory_response(from_inv),
        transform_inventory_response(to_inv)
    ]

