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
        Create order from user's cart and reduce inventory.
        
        Steps:
        1. Get user's cart items
        2. Validate stock availability
        3. Reserve inventory
        4. Create order
        5. Clear cart
        6. Fulfill inventory (reduce stock)
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
        for cart_item in cart.items:
            product = cart_item.product
            
            # Get inventory for this product
            inventory = db.query(Inventory).filter(
                Inventory.product_id == product.id
            ).first()
            
            if not inventory:
                raise ValidationError(
                    f"No inventory record found for product '{product.name}'. "
                    "Please contact support."
                )
            
            available = inventory.available_quantity
            if available < cart_item.quantity:
                raise ValidationError(
                    f"Insufficient stock for '{product.name}'. "
                    f"Available: {available}, Requested: {cart_item.quantity}"
                )

        # 3. Reserve inventory for all items first
        reserved_items = []
        try:
            for cart_item in cart.items:
                inventory = db.query(Inventory).filter(
                    Inventory.product_id == cart_item.product_id
                ).first()
                
                if not inventory.reserve_quantity(cart_item.quantity):
                    raise ValidationError(
                        f"Failed to reserve stock for '{cart_item.product.name}'"
                    )
                
                reserved_items.append((inventory, cart_item.quantity))
                db.flush()
        
        except Exception as e:
            # Rollback reservations on error
            for inventory, quantity in reserved_items:
                inventory.release_quantity(quantity)
            db.rollback()
            raise e

        # 4. Create order
        order_number = OrderService._generate_order_number()
        
        # Calculate totals
        subtotal = float(cart.total_amount)
        tax_amount = 0.0  # TODO: Implement tax calculation
        shipping_amount = 0.0  # TODO: Implement shipping calculation
        discount_amount = 0.0  # TODO: Implement discount logic
        total_amount = subtotal + tax_amount + shipping_amount - discount_amount

        # Create order
        order = Order(
            order_number=order_number,
            user_id=current_user.id,
            status=OrderStatus.PENDING.value,
            subtotal=subtotal,
            tax_amount=tax_amount,
            shipping_amount=shipping_amount,
            discount_amount=discount_amount,
            total_amount=total_amount,
            payment_status=PaymentStatus.PENDING.value,
            shipping_address_id=checkout_data.shipping_address_id,
            billing_address_id=checkout_data.billing_address_id or checkout_data.shipping_address_id,
            notes=checkout_data.notes
        )
        
        db.add(order)
        db.flush()

        # Create order items from cart items
        for cart_item in cart.items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=cart_item.product_id,
                variant_id=cart_item.variant_id,
                product_name=cart_item.product.name,
                product_sku=cart_item.variant.sku if cart_item.variant else None,
                variant_attributes=cart_item.variant.attributes if cart_item.variant else None,
                quantity=cart_item.quantity,
                unit_price=float(cart_item.price),
                total_price=float(cart_item.total_price)
            )
            db.add(order_item)

        db.flush()

        # 5. Fulfill inventory (reduce both reserved and stock quantities)
        for cart_item in cart.items:
            inventory = db.query(Inventory).filter(
                Inventory.product_id == cart_item.product_id
            ).first()
            
            # Reduce both reserved and stock
            inventory.reserved_quantity -= cart_item.quantity
            inventory.stock_quantity -= cart_item.quantity
            
            db.flush()

            # Log inventory fulfillment
            AuditLogService.log_create(
                db=db,
                user_id=current_user.id,
                entity_type="ORDER_FULFILLED",
                entity_id=inventory.id,
                new_values=f"Fulfilled {cart_item.quantity} units for order {order.order_number}. "
                        f"Stock: {inventory.stock_quantity}, Reserved: {inventory.reserved_quantity}"
            )

        # 6. Clear cart
        cart.items.clear()
        db.flush()

        # Log order creation
        AuditLogService.log_create(
            db=db,
            user_id=current_user.id,
            entity_type="Order",
            entity_id=order.id,
            entity_uuid=str(order.id),
            new_values={
                "order_number": order.order_number,
                "total_amount": float(order.total_amount),
                "status": order.status,
                "items_count": len(order.items)
            },
            ip_address=ip_address,
            user_agent=user_agent
        )

        db.commit()
        db.refresh(order)
        
        return order

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
            selectinload(Order.items)
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
            selectinload(Order.items)
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
            "payment_status": order.payment_status
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
            "payment_status": order.payment_status
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
