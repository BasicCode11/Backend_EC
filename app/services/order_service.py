from typing import List, Optional, Tuple
from sqlalchemy import select, func, or_, and_, desc, asc
from sqlalchemy.orm import Session, selectinload
from datetime import datetime
import secrets

from app.models.order import Order, OrderStatus, PaymentStatus
from app.models.order_item import OrderItem
from app.models.shopping_cart import ShoppingCart
from app.models.cart_item import CartItem
from app.models.user import User
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.inventory import Inventory
from app.schemas.order import (
    OrderCreate,
    OrderUpdate,
    CheckoutRequest,
    OrderSearchParams,
    OrderItemCreate
)
from app.core.exceptions import ValidationError, NotFoundError
from app.services.audit_log_service import AuditLogService
from app.services.inventory_service import InventoryService
from app.services.stock_validation_service import StockValidationService


class OrderService:
    """Service layer for order operations with automatic inventory management."""

    @staticmethod
    def _generate_order_number() -> str:
        """Generate unique order number"""
        timestamp = datetime.now().strftime("%Y%m%d")
        random_suffix = secrets.token_hex(4).upper()
        return f"ORD-{timestamp}-{random_suffix}"

    @staticmethod
    def create_from_checkout(
        db: Session,
        checkout_data: CheckoutRequest,
        current_user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Order:
        """
        Create order from user's cart, validate stock, and create order items.
        This process is done within a single transaction to ensure data integrity.
        """
        # 1. Get user's cart
        cart = db.query(ShoppingCart).filter(
            ShoppingCart.user_id == current_user.id
        ).options(
            selectinload(ShoppingCart.items).selectinload(CartItem.product),
            selectinload(ShoppingCart.items).selectinload(CartItem.variant)
        ).first()

        if not cart or cart.is_empty:
            raise ValidationError("Cart is empty. Add items before checkout.")

        # 2. Validate stock availability for all items
        for item in cart.items:
            if not item.variant_id:
                raise ValidationError(f"Product '{item.product.name}' in cart is missing a variant selection.")
            
            total_available_stock = db.query(func.sum(Inventory.available_quantity)).filter(
                Inventory.variant_id == item.variant_id
            ).scalar() or 0

            if total_available_stock < item.quantity:
                raise ValidationError(
                    f"Insufficient stock for '{item.product.name} - {item.variant.variant_name}'. "
                    f"Available: {total_available_stock}, Requested: {item.quantity}"
                )

        # 3. Create the Order
        try:
            # Calculate totals
            subtotal = cart.total_amount
            tax_amount = 0.0  # Placeholder
            shipping_amount = 0.0  # Placeholder
            discount_amount = 0.0  # Placeholder
            total_amount = subtotal + tax_amount + shipping_amount - discount_amount

            order = Order(
                order_number=OrderService._generate_order_number(),
                user_id=current_user.id,
                status=OrderStatus.PROCESSING.value,
                payment_status=PaymentStatus.PENDING.value, # Assuming payment is successful
                subtotal=subtotal,
                tax_amount=tax_amount,
                shipping_amount=shipping_amount,
                discount_amount=discount_amount,
                total_amount=total_amount,
                shipping_address_id=checkout_data.shipping_address_id,
                billing_address_id=checkout_data.billing_address_id or checkout_data.shipping_address_id,
                notes=checkout_data.notes
            )
            db.add(order)
            db.flush()

            # 4. Create OrderItems and reduce stock
            for item in cart.items:
                # Create OrderItem, freezing the data
                variant_attrs = {
                    "color": item.variant.color,
                    "size": item.variant.size,
                    "weight": item.variant.weight,
                } if item.variant else {}

                order_item = OrderItem(
                    order_id=order.id,
                    product_id=item.product_id,
                    variant_id=item.variant_id,
                    product_name=item.product.name,
                    product_sku=item.variant.sku if item.variant else item.product.sku, # Assuming product might have a base SKU
                    variant_attributes=variant_attrs,
                    quantity=item.quantity,
                    unit_price=item.price,
                    total_price=item.total_price
                )
                db.add(order_item)
                
                # Reduce stock from inventory records for this variant
                quantity_to_reduce = item.quantity
                inventories = db.query(Inventory).filter(
                    Inventory.variant_id == item.variant_id,
                    Inventory.available_quantity > 0
                ).order_by(Inventory.created_at).all() # FIFO

                for inv in inventories:
                    if quantity_to_reduce == 0:
                        break
                    
                    reducible = min(inv.available_quantity, quantity_to_reduce)
                    inv.stock_quantity -= reducible
                    quantity_to_reduce -= reducible
            
            # 5. Clear the cart
            db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
            
            # 6. Log and Commit
            AuditLogService.log_create(
                db=db,
                user_id=current_user.id,
                entity_type="Order",
                entity_id=order.id,
                new_values={
                    "order_number": order.order_number,
                    "total_amount": float(order.total_amount),
                    "status": order.status,
                },
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            db.commit()
            db.refresh(order)
            return order

        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def get_fordashboard(db: Session):
        base_query = db.query(Order).options(selectinload(Order.items))

        total = base_query.count()
        orders = base_query.order_by(Order.created_at.desc()).all()

        return orders, total



    @staticmethod
    def get_all(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        user_id: Optional[int] = None,
        status: Optional[str] = None,
        payment_status: Optional[str] = None
    ) -> Tuple[List[Order], int]:
        """Get all orders with optional filters"""
        query = select(Order).options(
            selectinload(Order.items),
            selectinload(Order.user)
        )

        if user_id:
            query = query.where(Order.user_id == user_id)
        if status:
            query = query.where(Order.status == status)
        if payment_status:
            query = query.where(Order.payment_status == payment_status)

        count_query = select(func.count()).select_from(query.subquery())
        total = db.execute(count_query).scalar()

        query = query.order_by(desc(Order.created_at)).offset(skip).limit(limit)
        orders = db.execute(query).scalars().all()

        return orders, total

    @staticmethod
    def get_by_id(db: Session, order_id: int) -> Optional[Order]:
        """Get order by ID with items"""
        return db.query(Order).options(
            selectinload(Order.items),
            selectinload(Order.user)
        ).filter(Order.id == order_id).first()

    @staticmethod
    def get_by_order_number(db: Session, order_number: str) -> Optional[Order]:
        """Get order by order number"""
        return db.query(Order).options(
            selectinload(Order.items),
            selectinload(Order.user)
        ).filter(Order.order_number == order_number).first()

    @staticmethod
    def update(
        db: Session,
        order_id: int,
        order_data: OrderUpdate,
        current_user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Order:
        """Update order"""
        order = OrderService.get_by_id(db, order_id)
        if not order:
            raise NotFoundError(f"Order with id {order_id} not found")

        old_values = {
            "status": order.status,
        }

        # Update fields
        update_data = order_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field in ['status', 'payment_status'] and value:
                setattr(order, field, value.value)
            else:
                setattr(order, field, value)

        db.flush()

        new_values = {
            "status": order.status,
        }

        AuditLogService.log_update(
            db=db,
            user_id=current_user.id,
            entity_type="Order",
            entity_id=order.id,
            entity_uuid=str(order.id),
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent
        )

        db.commit()
        db.refresh(order)
        return order

    @staticmethod
    def cancel_order(
        db: Session,
        order_id: int,
        current_user: User,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Order:
        """
        Cancel order and restore inventory.
        
        Only pending and processing orders can be cancelled.
        """
        order = OrderService.get_by_id(db, order_id)
        if not order:
            raise NotFoundError(f"Order with id {order_id} not found")

        if not order.can_be_cancelled:
            raise ValidationError(
                f"Order with status '{order.status}' cannot be cancelled. "
                "Only pending or processing orders can be cancelled."
            )

        # Restore inventory
        for order_item in order.items:
            inventory = db.query(Inventory).filter(
                Inventory.product_id == order_item.product_id
            ).first()
            
            if inventory:
                # Add stock back
                inventory.stock_quantity += order_item.quantity
                db.flush()

                AuditLogService.log_action(
                    db=db,
                    user_id=current_user.id,
                    action="STOCK_RESTORED",
                    resource_type="Inventory",
                    resource_id=inventory.id,
                    details=f"Restored {order_item.quantity} units from cancelled order {order.order_number}"
                )

        # Update order status
        order.status = OrderStatus.CANCELLED.value
        db.flush()

        AuditLogService.log_action(
            db=db,
            user_id=current_user.id,
            action="ORDER_CANCELLED",
            resource_type="Order",
            resource_id=order.id,
            details=f"Order {order.order_number} cancelled. Reason: {reason or 'Not provided'}",
            ip_address=ip_address,
            user_agent=user_agent
        )

        db.commit()
        db.refresh(order)
        
        return order

    @staticmethod
    def get_user_orders(
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[Order], int]:
        """Get orders for a specific user"""
        return OrderService.get_all(db, skip, limit, user_id=user_id)

    @staticmethod
    def get_statistics(db: Session, user_id: Optional[int] = None) -> dict:
        """Get order statistics"""
        query = select(func.count(Order.id)).select_from(Order)
        
        if user_id:
            query = query.where(Order.user_id == user_id)
        
        total_orders = db.execute(query).scalar()
        
        # Count by status
        pending = db.execute(query.where(Order.status == OrderStatus.PENDING.value)).scalar()
        processing = db.execute(query.where(Order.status == OrderStatus.PROCESSING.value)).scalar()
        shipped = db.execute(query.where(Order.status == OrderStatus.SHIPPED.value)).scalar()
        delivered = db.execute(query.where(Order.status == OrderStatus.DELIVERED.value)).scalar()
        cancelled = db.execute(query.where(Order.status == OrderStatus.CANCELLED.value)).scalar()
        
        # Total revenue
        revenue_query = select(func.sum(Order.total_amount)).where(
            Order.payment_status == PaymentStatus.PAID.value
        )
        if user_id:
            revenue_query = revenue_query.where(Order.user_id == user_id)
        
        total_revenue = db.execute(revenue_query).scalar() or 0

        return {
            "total_orders": total_orders,
            "pending": pending,
            "processing": processing,
            "shipped": shipped,
            "delivered": delivered,
            "cancelled": cancelled,
            "total_revenue": float(total_revenue)
        }
