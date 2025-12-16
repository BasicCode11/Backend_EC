# app/seed/seed.py
from datetime import datetime, timezone
from typing import List, Dict, Any

from sqlalchemy.orm import Session
from app.database import get_db
from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User




class DataFactory:
    """Factory class for generating seed data."""



    @staticmethod
    def generate_permissions() -> List[Dict[str, Any]]:
        return [
            # User Management Permissions
            {"name": "users:create"},
            {"name": "users:read"},
            {"name": "users:update"},
            {"name": "users:delete"},
            {"name": "users:list"},
            {"name": "users:search"},
            
            # Role Management Permissions
            {"name": "roles:create"},
            {"name": "roles:read"},
            {"name": "roles:update"},
            {"name": "roles:delete"},
            {"name": "roles:list"},
            
            # Permission Management
            {"name": "permissions:create"},
            {"name": "permissions:read"},
            {"name": "permissions:update"},
            {"name": "permissions:delete"},
            {"name": "permissions:list"},
            
            # Product Management Permissions
            {"name": "products:create"},
            {"name": "products:read"},
            {"name": "products:update"},
            {"name": "products:delete"},
            {"name": "products:list"},
            {"name": "products:search"},
            
            # Category Management
            {"name": "categories:create"},
            {"name": "categories:read"},
            {"name": "categories:update"},
            {"name": "categories:delete"},
            {"name": "categories:list"},
            
            # Order Management
            {"name": "orders:create"},
            {"name": "orders:read"},
            {"name": "orders:update"},
            {"name": "orders:delete"},
            {"name": "orders:list"},
            {"name": "orders:search"},
            {"name": "orders:status_update"},
            
            # Shopping Cart Permissions
            {"name": "cart:create"},
            {"name": "cart:read"},
            {"name": "cart:update"},
            {"name": "cart:delete"},
            {"name": "cart:add_item"},
            {"name": "cart:remove_item"},
            {"name": "cart:clear"},
            
            # Payment Management
            {"name": "payments:create"},
            {"name": "payments:read"},
            {"name": "payments:update"},
            {"name": "payments:delete"},
            {"name": "payments:list"},
            
            # Inventory Management
            {"name": "inventory:create"},
            {"name": "inventory:read"},
            {"name": "inventory:update"},
            {"name": "inventory:delete"},
            {"name": "inventory:list"},
            {"name": "inventory:adjust"},
            
            # Review Management
            {"name": "reviews:create"},
            {"name": "reviews:read"},
            {"name": "reviews:update"},
            {"name": "reviews:delete"},
            {"name": "reviews:list"},
            
            # Discount Management
            {"name": "discounts:create"},
            {"name": "discounts:read"},
            {"name": "discounts:update"},
            {"name": "discounts:delete"},
            {"name": "discounts:list"},
            
            # Analytics and Reports
            {"name": "analytics:read"},
            {"name": "reports:generate"},
            {"name": "reports:export"},
            
            # System Administration
            {"name": "system:settings"},
            {"name": "system:logs"},
            {"name": "system:backup"},
            {"name": "system:maintenance"},

            #authid log 
            {"name": "audit_logs:create"},
            {"name": "audit_logs:read"},
            {"name": "audit_logs:update"},
            {"name": "audit_logs:delete"},

            {"name": "brands:create"},
            {"name": "brands:read"},
            {"name": "brands:update"},
            {"name": "brands:delete"},
            {"name": "brands:list"},
            {"name": "brands:search"},

            {"name": "variants:create"},
            {"name": "variants:read"},
            {"name": "variants:update"},
            {"name": "variants:delete"},

            {"name": "product_image:read"},
            {"name": "product_image:create"},
            {"name": "product_image:update"},
            {"name": "product_image:delete"},

            {"name": "customer:read"},
            {"name": "customer:create"},
            {"name": "customer:update"},
            {"name": "customer:delete"},

            {"name": "email:read"},
            {"name": "email:create"},
            {"name": "email:update"},
            {"name": "email:delete"},
        ]

    @staticmethod
    def generate_roles() -> List[Dict[str, Any]]:
        return [
            {
                "name": "admin",
                "description": "Administrator with full system access",
                "permissions": [
                    # User Management
                    {"name": "users:create"},
                    {"name": "users:read"},
                    {"name": "users:update"},
                    {"name": "users:delete"},
                    {"name": "users:list"},
                    {"name": "users:search"},
                    
                    # Role Management
                    {"name": "roles:create"},
                    {"name": "roles:read"},
                    {"name": "roles:update"},
                    {"name": "roles:delete"},
                    {"name": "roles:list"},
                    
                    # Permission Management
                    {"name": "permissions:create"},
                    {"name": "permissions:read"},
                    {"name": "permissions:update"},
                    {"name": "permissions:delete"},
                    {"name": "permissions:list"},
                    
                    # Product Management
                    {"name": "products:create"},
                    {"name": "products:read"},
                    {"name": "products:update"},
                    {"name": "products:delete"},
                    {"name": "products:list"},
                    {"name": "products:search"},
                    
                    # Category Management
                    {"name": "categories:create"},
                    {"name": "categories:read"},
                    {"name": "categories:update"},
                    {"name": "categories:delete"},
                    {"name": "categories:list"},
                    
                    # Order Management
                    {"name": "orders:create"},
                    {"name": "orders:read"},
                    {"name": "orders:update"},
                    {"name": "orders:delete"},
                    {"name": "orders:list"},
                    {"name": "orders:search"},
                    {"name": "orders:status_update"},
                    
                    # Payment Management
                    {"name": "payments:create"},
                    {"name": "payments:read"},
                    {"name": "payments:update"},
                    {"name": "payments:delete"},
                    {"name": "payments:list"},
                    
                    # Inventory Management
                    {"name": "inventory:create"},
                    {"name": "inventory:read"},
                    {"name": "inventory:update"},
                    {"name": "inventory:delete"},
                    {"name": "inventory:list"},
                    {"name": "inventory:adjust"},
                    
                    # Review Management
                    {"name": "reviews:create"},
                    {"name": "reviews:read"},
                    {"name": "reviews:update"},
                    {"name": "reviews:delete"},
                    {"name": "reviews:list"},
                    
                    # Discount Management
                    {"name": "discounts:create"},
                    {"name": "discounts:read"},
                    {"name": "discounts:update"},
                    {"name": "discounts:delete"},
                    {"name": "discounts:list"},
                    
                    # Analytics and Reports
                    {"name": "analytics:read"},
                    {"name": "reports:generate"},
                    {"name": "reports:export"},
                    
                    # System Administration
                    {"name": "system:settings"},
                    {"name": "system:logs"},
                    {"name": "system:backup"},
                    {"name": "system:maintenance"},

                    #authid log 
                    {"name": "audit_logs:create"},
                    {"name": "audit_logs:read"},
                    {"name": "audit_logs:update"},
                    {"name": "audit_logs:delete"},
                    #brand
                    {"name": "brands:create"},
                    {"name": "brands:read"},
                    {"name": "brands:update"},
                    {"name": "brands:delete"},
                    {"name": "brands:list"},
                    {"name": "brands:search"},
                    #variant
                    {"name": "variants:create"},
                    {"name": "variants:read"},
                    {"name": "variants:update"},
                    {"name": "variants:delete"},
                    {"name": "product_image:read"},
                    {"name": "product_image:create"},
                    {"name": "product_image:update"},
                    {"name": "product_image:delete"},

                    {"name": "customer:read"},
                    {"name": "customer:create"},
                    {"name": "customer:update"},
                    {"name": "customer:delete"},
                    
                    {"name": "email:read"},
                    {"name": "email:create"},
                    {"name": "email:update"},
                    {"name": "email:delete"},
                ],
            },
            {
                "name": "customer",
                "description": "Customer with shopping and order permissions",
                "permissions": [
                    # Shopping Cart
                    {"name": "cart:create"},
                    {"name": "cart:read"},
                    {"name": "cart:update"},
                    {"name": "cart:delete"},
                    {"name": "cart:add_item"},
                    {"name": "cart:remove_item"},
                    {"name": "cart:clear"},
                    
                    # Orders
                    {"name": "orders:create"},
                    {"name": "orders:read"},
                    
                    # Products (read only)
                    {"name": "products:read"},
                    {"name": "products:list"},
                    {"name": "products:search"},
                    
                    # Categories (read only)
                    {"name": "categories:read"},
                    {"name": "categories:list"},
                    
                    # Reviews
                    {"name": "reviews:create"},
                    {"name": "reviews:read"},
                    {"name": "reviews:update"},
                    {"name": "reviews:delete"},
                    {"name": "reviews:list"},
                    
                    # Payments
                    {"name": "payments:create"},
                    {"name": "payments:read"},
                ],
            }
        ]

    @staticmethod

    def generate_users(num_users: int = 3) -> List[Dict[str, Any]]:
        return [
            {
                "email": "kang@example.com",
                "password": "admin123",  # raw password, hashed later
                "first_name": "Admin",
                "last_name": "User",
                "phone": "+1234567890",
                "role_name": "admin",
            },
            
        ]

        
