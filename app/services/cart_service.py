from typing import Optional
from sqlalchemy.orm import Session, selectinload
from app.models.shopping_cart import ShoppingCart
from app.models.cart_item import CartItem
from app.models.user import User
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.inventory import Inventory
from app.schemas.cart import AddToCartRequest, UpdateCartItemRequest
from app.core.exceptions import ValidationError, NotFoundError


class CartService:
    """Service for shopping cart operations"""

    @staticmethod
    def get_or_create_cart(db: Session, user: Optional[User] = None, session_id: Optional[str] = None) -> ShoppingCart:
        """Get or create shopping cart for user or session"""
        if user:
            cart = db.query(ShoppingCart).filter(
                ShoppingCart.user_id == user.id
            ).options(
                selectinload(ShoppingCart.items).selectinload(CartItem.product),
                selectinload(ShoppingCart.items).selectinload(CartItem.variant)
            ).first()
            
            if not cart:
                cart = ShoppingCart(user_id=user.id)
                db.add(cart)
                db.flush()
        elif session_id:
            cart = db.query(ShoppingCart).filter(
                ShoppingCart.session_id == session_id
            ).options(
                selectinload(ShoppingCart.items).selectinload(CartItem.product),
                selectinload(ShoppingCart.items).selectinload(CartItem.variant)
            ).first()
            
            if not cart:
                cart = ShoppingCart(session_id=session_id)
                db.add(cart)
                db.flush()
        else:
            raise ValidationError("Either user or session_id must be provided")
        
        return cart

    @staticmethod
    def add_to_cart(
        db: Session,
        user: Optional[User],
        cart_data: AddToCartRequest,
        session_id: Optional[str] = None
    ) -> ShoppingCart:
        """Add item to cart"""
        # Get or create cart
        cart = CartService.get_or_create_cart(db, user, session_id)
        
        # Validate product exists
        product = db.query(Product).filter(Product.id == cart_data.product_id).first()
        if not product:
            raise NotFoundError(f"Product with id {cart_data.product_id} not found")
        
        # Validate variant if provided
        variant = None
        if cart_data.variant_id:
            variant = db.query(ProductVariant).filter(
                ProductVariant.id == cart_data.variant_id,
                ProductVariant.product_id == cart_data.product_id
            ).first()
            if not variant:
                raise NotFoundError(f"Variant with id {cart_data.variant_id} not found")
        
        # Check stock availability
        inventory = db.query(Inventory).filter(
            Inventory.product_id == cart_data.product_id
        ).first()
        
        if not inventory:
            raise ValidationError(f"No inventory found for product '{product.name}'")
        
        if inventory.available_quantity < cart_data.quantity:
            raise ValidationError(
                f"Insufficient stock. Available: {inventory.available_quantity}, "
                f"Requested: {cart_data.quantity}"
            )
        
        # Check if item already in cart
        # Handle None variant_id properly for SQL comparison
        if cart_data.variant_id is None:
            existing_item = db.query(CartItem).filter(
                CartItem.cart_id == cart.id,
                CartItem.product_id == cart_data.product_id,
                CartItem.variant_id.is_(None)
            ).first()
        else:
            existing_item = db.query(CartItem).filter(
                CartItem.cart_id == cart.id,
                CartItem.product_id == cart_data.product_id,
                CartItem.variant_id == cart_data.variant_id
            ).first()
        
        # Determine price
        price = variant.effective_price if variant else product.price
        
        if existing_item:
            # Update quantity
            new_quantity = existing_item.quantity + cart_data.quantity
            
            # Check stock for new total
            if inventory.available_quantity < new_quantity:
                raise ValidationError(
                    f"Insufficient stock. Available: {inventory.available_quantity}, "
                    f"Cart has: {existing_item.quantity}, Trying to add: {cart_data.quantity}"
                )
            
            existing_item.quantity = new_quantity
            existing_item.price = price
        else:
            # Create new cart item
            # Ensure variant_id is None (not 0) if no variant selected
            variant_id_value = cart_data.variant_id if cart_data.variant_id else None
            
            cart_item = CartItem(
                cart_id=cart.id,
                product_id=cart_data.product_id,
                variant_id=variant_id_value,
                quantity=cart_data.quantity,
                price=price
            )
            db.add(cart_item)
        
        db.commit()
        db.refresh(cart)
        return cart

    @staticmethod
    def update_cart_item(
        db: Session,
        user: Optional[User],
        cart_item_id: int,
        update_data: UpdateCartItemRequest,
        session_id: Optional[str] = None
    ) -> ShoppingCart:
        """Update cart item quantity"""
        # Get cart
        cart = CartService.get_or_create_cart(db, user, session_id)
        
        # Get cart item
        cart_item = db.query(CartItem).filter(
            CartItem.id == cart_item_id,
            CartItem.cart_id == cart.id
        ).first()
        
        if not cart_item:
            raise NotFoundError(f"Cart item with id {cart_item_id} not found")
        
        # Check stock availability
        inventory = db.query(Inventory).filter(
            Inventory.product_id == cart_item.product_id
        ).first()
        
        if inventory and inventory.available_quantity < update_data.quantity:
            raise ValidationError(
                f"Insufficient stock. Available: {inventory.available_quantity}, "
                f"Requested: {update_data.quantity}"
            )
        
        cart_item.quantity = update_data.quantity
        
        db.commit()
        db.refresh(cart)
        return cart

    @staticmethod
    def remove_from_cart(
        db: Session,
        user: Optional[User],
        cart_item_id: int,
        session_id: Optional[str] = None
    ) -> ShoppingCart:
        """Remove item from cart"""
        # Get cart
        cart = CartService.get_or_create_cart(db, user, session_id)
        
        # Get and delete cart item
        cart_item = db.query(CartItem).filter(
            CartItem.id == cart_item_id,
            CartItem.cart_id == cart.id
        ).first()
        
        if not cart_item:
            raise NotFoundError(f"Cart item with id {cart_item_id} not found")
        
        db.delete(cart_item)
        db.commit()
        db.refresh(cart)
        return cart

    @staticmethod
    def clear_cart(
        db: Session,
        user: Optional[User],
        session_id: Optional[str] = None
    ) -> ShoppingCart:
        """Clear all items from cart"""
        cart = CartService.get_or_create_cart(db, user, session_id)
        
        # Delete all cart items
        db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
        
        db.commit()
        db.refresh(cart)
        return cart

    @staticmethod
    def get_cart(
        db: Session,
        user: Optional[User],
        session_id: Optional[str] = None
    ) -> ShoppingCart:
        """Get user's shopping cart"""
        return CartService.get_or_create_cart(db, user, session_id)

    @staticmethod
    def merge_carts(db: Session, user: User, session_id: str) -> ShoppingCart:
        """Merge guest cart into user cart after login"""
        # Get user cart
        user_cart = CartService.get_or_create_cart(db, user=user)
        
        # Get guest cart
        guest_cart = db.query(ShoppingCart).filter(
            ShoppingCart.session_id == session_id
        ).options(
            selectinload(ShoppingCart.items)
        ).first()
        
        if not guest_cart or not guest_cart.items:
            return user_cart
        
        # Merge items
        for guest_item in guest_cart.items:
            # Check if item exists in user cart
            # Handle None variant_id properly
            if guest_item.variant_id is None:
                existing_item = db.query(CartItem).filter(
                    CartItem.cart_id == user_cart.id,
                    CartItem.product_id == guest_item.product_id,
                    CartItem.variant_id.is_(None)
                ).first()
            else:
                existing_item = db.query(CartItem).filter(
                    CartItem.cart_id == user_cart.id,
                    CartItem.product_id == guest_item.product_id,
                    CartItem.variant_id == guest_item.variant_id
                ).first()
            
            if existing_item:
                # Update quantity
                existing_item.quantity += guest_item.quantity
            else:
                # Move item to user cart
                guest_item.cart_id = user_cart.id
        
        # Delete guest cart
        db.delete(guest_cart)
        
        db.commit()
        db.refresh(user_cart)
        return user_cart
