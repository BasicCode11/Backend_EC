# Import all models to ensure they are registered with SQLAlchemy
from .user import User
from .role import Role
from .permission import Permission
from .role_has_permision import role_has_permission
from .user_address import UserAddress, AddressType
from .category import Category
from .product import Product, ProductStatus
from .product_image import ProductImage
from .inventory import Inventory
from .product_variant import ProductVariant
from .shopping_cart import ShoppingCart
from .cart_item import CartItem
from .order import Order, OrderStatus, PaymentStatus
from .order_item import OrderItem
from .payment import Payment, PaymentMethod, PaymentStatus as PaymentStatusEnum
from .review import Review
from .discount import Discount, DiscountType, ApplyTo
from .discount_application import DiscountApplication
from .email_notification import EmailNotification, EmailStatus
from .audit_log import AuditLog

__all__ = [
    "User",
    "Role", 
    "Permission",
    "role_has_permission",
    "UserAddress",
    "AddressType",
    "Category",
    "Product",
    "ProductStatus",
    "ProductImage",
    "Inventory",
    "ProductVariant",
    "ShoppingCart",
    "CartItem",
    "Order",
    "OrderStatus",
    "PaymentStatus",
    "OrderItem",
    "Payment",
    "PaymentMethod",
    "PaymentStatusEnum",
    "Review",
    "Discount",
    "DiscountType",
    "ApplyTo",
    "DiscountApplication",
    "EmailNotification",
    "EmailStatus",
    "AuditLog",
]
