from typing import List, Optional
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import and_

from app.models.wishlist import Wishlist
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.inventory import Inventory
from app.schemas.wishlist import WishlistItemAdd
from app.core.exceptions import ValidationError, NotFoundError


class WishlistService:
    """Service for managing user wishlists"""

    @staticmethod
    def add_to_wishlist(
        db: Session,
        user_id: int,
        wishlist_data: WishlistItemAdd
    ) -> Wishlist:
        """Add item to user's wishlist"""
        # Check if product exists
        product = db.query(Product).filter(Product.id == wishlist_data.product_id).first()
        if not product:
            raise NotFoundError(f"Product with ID {wishlist_data.product_id} not found")
        
        # Check if variant exists (if provided)
        if wishlist_data.variant_id:
            variant = db.query(ProductVariant).filter(
                and_(
                    ProductVariant.id == wishlist_data.variant_id,
                    ProductVariant.product_id == wishlist_data.product_id
                )
            ).first()
            
            if not variant:
                raise NotFoundError(f"Variant with ID {wishlist_data.variant_id} not found")
        
        # Check if already in wishlist
        # Handle None variant_id properly for SQL comparison
        if wishlist_data.variant_id is None:
            existing = db.query(Wishlist).filter(
                and_(
                    Wishlist.user_id == user_id,
                    Wishlist.product_id == wishlist_data.product_id,
                    Wishlist.variant_id.is_(None)
                )
            ).first()
        else:
            existing = db.query(Wishlist).filter(
                and_(
                    Wishlist.user_id == user_id,
                    Wishlist.product_id == wishlist_data.product_id,
                    Wishlist.variant_id == wishlist_data.variant_id
                )
            ).first()
        
        if existing:
            raise ValidationError("Item already in wishlist")
        
        # Add to wishlist
        # Ensure variant_id is None (not 0) if no variant selected
        variant_id_value = wishlist_data.variant_id if wishlist_data.variant_id else None
        
        wishlist_item = Wishlist(
            user_id=user_id,
            product_id=wishlist_data.product_id,
            variant_id=variant_id_value
        )
        
        db.add(wishlist_item)
        db.commit()
        db.refresh(wishlist_item)
        
        return wishlist_item

    @staticmethod
    def get_user_wishlist(db: Session, user_id: int) -> List[Wishlist]:
        """Get all items in user's wishlist"""
        wishlist_items = db.query(Wishlist).filter(
            Wishlist.user_id == user_id
        ).options(
            selectinload(Wishlist.product),
            selectinload(Wishlist.variant)
        ).order_by(
            Wishlist.created_at.desc()
        ).all()
        
        return wishlist_items

    @staticmethod
    def remove_from_wishlist(
        db: Session,
        user_id: int,
        wishlist_item_id: int
    ) -> None:
        """Remove item from wishlist"""
        wishlist_item = db.query(Wishlist).filter(
            and_(
                Wishlist.id == wishlist_item_id,
                Wishlist.user_id == user_id
            )
        ).first()
        
        if not wishlist_item:
            raise NotFoundError("Wishlist item not found")
        
        db.delete(wishlist_item)
        db.commit()

    @staticmethod
    def remove_product_from_wishlist(
        db: Session,
        user_id: int,
        product_id: int,
        variant_id: Optional[int] = None
    ) -> None:
        """Remove product from wishlist by product_id"""
        # Handle None variant_id properly
        if variant_id is None:
            query = db.query(Wishlist).filter(
                and_(
                    Wishlist.user_id == user_id,
                    Wishlist.product_id == product_id,
                    Wishlist.variant_id.is_(None)
                )
            )
        else:
            query = db.query(Wishlist).filter(
                and_(
                    Wishlist.user_id == user_id,
                    Wishlist.product_id == product_id,
                    Wishlist.variant_id == variant_id
                )
            )
        
        wishlist_item = query.first()
        
        if not wishlist_item:
            raise NotFoundError("Wishlist item not found")
        
        db.delete(wishlist_item)
        db.commit()

    @staticmethod
    def clear_wishlist(db: Session, user_id: int) -> int:
        """Clear all items from user's wishlist"""
        count = db.query(Wishlist).filter(
            Wishlist.user_id == user_id
        ).delete()
        
        db.commit()
        return count

    @staticmethod
    def get_wishlist_count(db: Session, user_id: int) -> int:
        """Get count of items in wishlist"""
        count = db.query(Wishlist).filter(
            Wishlist.user_id == user_id
        ).count()
        
        return count

    @staticmethod
    def is_in_wishlist(
        db: Session,
        user_id: int,
        product_id: int,
        variant_id: Optional[int] = None
    ) -> bool:
        """Check if product is in user's wishlist"""
        # Handle None variant_id properly
        if variant_id is None:
            query = db.query(Wishlist).filter(
                and_(
                    Wishlist.user_id == user_id,
                    Wishlist.product_id == product_id,
                    Wishlist.variant_id.is_(None)
                )
            )
        else:
            query = db.query(Wishlist).filter(
                and_(
                    Wishlist.user_id == user_id,
                    Wishlist.product_id == product_id,
                    Wishlist.variant_id == variant_id
                )
            )
        
        return query.first() is not None

    @staticmethod
    def get_product_stock(db: Session, product_id: int) -> int:
        """Get available stock for product"""
        inventory = db.query(Inventory).filter(
            Inventory.product_id == product_id
        ).first()
        
        if not inventory:
            return 0
        
        return inventory.available_quantity
