"""
Stock Validation Service

Ensures that variant stock never exceeds product inventory stock.
Provides validation and synchronization utilities.
"""

from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.inventory import Inventory
from app.core.exceptions import ValidationError


class StockValidationService:
    """Service for stock validation and management"""

    @staticmethod
    def validate_variant_stock_against_inventory(
        db: Session,
        product_id: int,
        variant_id: Optional[int] = None,
        variant_stock: Optional[int] = None
    ) -> bool:
        """
        Validate that variant stock doesn't exceed product inventory.
        
        Args:
            db: Database session
            product_id: Product ID
            variant_id: Variant ID (optional, for update operations)
            variant_stock: Proposed variant stock (optional, for validation before save)
            
        Returns:
            bool: True if valid
            
        Raises:
            ValidationError: If validation fails
        """
        # Get product's total inventory
        inventory = db.query(Inventory).filter(
            Inventory.product_id == product_id
        ).first()
        
        if not inventory:
            raise ValidationError(
                f"No inventory found for product ID {product_id}. "
                "Please create inventory before setting variant stock."
            )
        
        total_inventory = inventory.stock_quantity
        
        # Get all variants for this product
        variants_query = db.query(ProductVariant).filter(
            ProductVariant.product_id == product_id
        )
        
        # Exclude the variant being updated
        if variant_id:
            variants_query = variants_query.filter(ProductVariant.id != variant_id)
        
        other_variants = variants_query.all()
        
        # Calculate total stock across all OTHER variants
        other_variants_total = sum(v.stock_quantity for v in other_variants)
        
        # Add the proposed variant stock
        proposed_total = other_variants_total + (variant_stock or 0)
        
        # Validate
        if proposed_total > total_inventory:
            raise ValidationError(
                f"Total variant stock ({proposed_total}) cannot exceed product inventory ({total_inventory}). "
                f"Other variants: {other_variants_total}, Proposed: {variant_stock}"
            )
        
        return True

    @staticmethod
    def get_available_stock_for_variant(
        db: Session,
        product_id: int,
        variant_id: Optional[int] = None
    ) -> int:
        """
        Get how much stock is available for a variant.
        
        Returns the difference between total inventory and allocated variant stock.
        
        Args:
            db: Database session
            product_id: Product ID
            variant_id: Variant ID (optional, to exclude this variant from calculation)
            
        Returns:
            int: Available stock for this variant
        """
        # Get product's total inventory
        inventory = db.query(Inventory).filter(
            Inventory.product_id == product_id
        ).first()
        
        if not inventory:
            return 0
        
        total_inventory = inventory.stock_quantity
        
        # Get all variants for this product
        variants_query = db.query(ProductVariant).filter(
            ProductVariant.product_id == product_id
        )
        
        # Exclude the variant being checked
        if variant_id:
            variants_query = variants_query.filter(ProductVariant.id != variant_id)
        
        other_variants = variants_query.all()
        
        # Calculate allocated stock
        allocated_stock = sum(v.stock_quantity for v in other_variants)
        
        # Return available
        return max(0, total_inventory - allocated_stock)

    @staticmethod
    def reduce_stock(
        db: Session,
        product_id: int,
        variant_id: Optional[int],
        quantity: int
    ) -> Tuple[Inventory, Optional[ProductVariant]]:
        """
        Reduce stock from both inventory and variant.
        
        This is called when an order is completed/fulfilled.
        
        Args:
            db: Database session
            product_id: Product ID
            variant_id: Variant ID (can be None if no variant selected)
            quantity: Quantity to reduce
            
        Returns:
            Tuple of (updated_inventory, updated_variant)
            
        Raises:
            ValidationError: If insufficient stock
        """
        # Get inventory
        inventory = db.query(Inventory).filter(
            Inventory.product_id == product_id
        ).first()
        
        if not inventory:
            raise ValidationError(f"No inventory found for product ID {product_id}")
        
        # Check inventory has enough stock
        if inventory.stock_quantity < quantity:
            raise ValidationError(
                f"Insufficient inventory stock. Available: {inventory.stock_quantity}, "
                f"Requested: {quantity}"
            )
        
        # Get variant if specified
        variant = None
        if variant_id:
            variant = db.query(ProductVariant).filter(
                ProductVariant.id == variant_id,
                ProductVariant.product_id == product_id
            ).first()
            
            if not variant:
                raise ValidationError(f"Variant ID {variant_id} not found for product")
            
            # Check variant has enough stock
            if variant.stock_quantity < quantity:
                raise ValidationError(
                    f"Insufficient variant stock. Available: {variant.stock_quantity}, "
                    f"Requested: {quantity}"
                )
            
            # Reduce variant stock
            variant.stock_quantity -= quantity
        
        # Reduce inventory stock
        inventory.stock_quantity -= quantity
        
        db.flush()
        
        return inventory, variant

    @staticmethod
    def check_stock_consistency(db: Session, product_id: int) -> dict:
        """
        Check stock consistency between inventory and variants.
        
        Returns a report of any discrepancies.
        
        Args:
            db: Database session
            product_id: Product ID
            
        Returns:
            dict: Consistency report
        """
        # Get inventory
        inventory = db.query(Inventory).filter(
            Inventory.product_id == product_id
        ).first()
        
        # Get all variants
        variants = db.query(ProductVariant).filter(
            ProductVariant.product_id == product_id
        ).all()
        
        # Calculate totals
        total_inventory = inventory.stock_quantity if inventory else 0
        total_variant_stock = sum(v.stock_quantity for v in variants)
        
        # Check consistency
        is_consistent = total_variant_stock <= total_inventory
        
        return {
            "product_id": product_id,
            "inventory_stock": total_inventory,
            "total_variant_stock": total_variant_stock,
            "available_unallocated": total_inventory - total_variant_stock,
            "is_consistent": is_consistent,
            "has_inventory": inventory is not None,
            "variant_count": len(variants),
            "variants": [
                {
                    "id": v.id,
                    "name": v.variant_name,
                    "sku": v.sku,
                    "stock": v.stock_quantity
                }
                for v in variants
            ]
        }

    @staticmethod
    def sync_variant_stock_to_inventory(
        db: Session,
        product_id: int,
        distribute_evenly: bool = False
    ) -> List[ProductVariant]:
        """
        Sync variant stock to match inventory constraints.
        
        If variant stock exceeds inventory, reduce proportionally.
        
        Args:
            db: Database session
            product_id: Product ID
            distribute_evenly: If True, distribute inventory evenly across variants
            
        Returns:
            List of updated variants
        """
        inventory = db.query(Inventory).filter(
            Inventory.product_id == product_id
        ).first()
        
        if not inventory:
            raise ValidationError(f"No inventory found for product ID {product_id}")
        
        variants = db.query(ProductVariant).filter(
            ProductVariant.product_id == product_id
        ).all()
        
        if not variants:
            return []
        
        total_inventory = inventory.stock_quantity
        
        if distribute_evenly:
            # Distribute evenly
            per_variant = total_inventory // len(variants)
            remainder = total_inventory % len(variants)
            
            for i, variant in enumerate(variants):
                variant.stock_quantity = per_variant + (1 if i < remainder else 0)
        else:
            # Proportional reduction if over limit
            total_variant_stock = sum(v.stock_quantity for v in variants)
            
            if total_variant_stock > total_inventory:
                # Reduce proportionally
                ratio = total_inventory / total_variant_stock
                for variant in variants:
                    variant.stock_quantity = int(variant.stock_quantity * ratio)
        
        db.flush()
        return variants
