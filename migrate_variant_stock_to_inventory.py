"""
Data Migration Script: Migrate Variant Stock to Inventory Table

This script migrates stock_quantity data from product_variants table
to the inventory table BEFORE running the schema migration that removes
the stock_quantity column.

Usage:
    python migrate_variant_stock_to_inventory.py

What it does:
1. Reads all variants with stock_quantity > 0
2. Creates corresponding inventory records
3. Links inventory to products (not individual variants)
4. Preserves variant SKUs in inventory records for tracking
"""

import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.database import get_db, engine
from app.models.product_variant import ProductVariant
from app.models.inventory import Inventory
from app.models.product import Product


def migrate_variant_stock_to_inventory():
    """Migrate stock from variants to inventory table"""
    
    # Create session
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        print("=" * 70)
        print("VARIANT STOCK TO INVENTORY MIGRATION")
        print("=" * 70)
        print()
        
        # Get all variants with stock
        variants_with_stock = db.query(ProductVariant).filter(
            ProductVariant.stock_quantity > 0
        ).all()
        
        if not variants_with_stock:
            print("✓ No variants with stock found. Nothing to migrate.")
            return
        
        print(f"Found {len(variants_with_stock)} variants with stock:")
        print()
        
        migrated_count = 0
        skipped_count = 0
        
        for variant in variants_with_stock:
            print(f"Variant ID: {variant.id}")
            print(f"  Product ID: {variant.product_id}")
            print(f"  Name: {variant.variant_name}")
            print(f"  SKU: {variant.sku or 'N/A'}")
            print(f"  Stock: {variant.stock_quantity}")
            
            # Check if inventory already exists for this product+sku combination
            existing_inventory = None
            if variant.sku:
                existing_inventory = db.query(Inventory).filter(
                    Inventory.product_id == variant.product_id,
                    Inventory.sku == variant.sku
                ).first()
            
            if existing_inventory:
                print(f"  → Skipping (inventory already exists: ID {existing_inventory.id})")
                skipped_count += 1
            else:
                # Create new inventory record
                new_inventory = Inventory(
                    product_id=variant.product_id,
                    stock_quantity=variant.stock_quantity,
                    reserved_quantity=0,
                    low_stock_threshold=10,
                    reorder_level=5,
                    sku=variant.sku,
                    location=f"Migrated from Variant ID {variant.id}"
                )
                db.add(new_inventory)
                print(f"  → Created inventory record")
                migrated_count += 1
            
            print()
        
        # Commit all changes
        if migrated_count > 0:
            db.commit()
            print(f"✓ Successfully migrated {migrated_count} variant stock records to inventory")
        
        if skipped_count > 0:
            print(f"⚠ Skipped {skipped_count} variants (inventory already exists)")
        
        print()
        print("=" * 70)
        print("MIGRATION COMPLETE")
        print("=" * 70)
        print()
        print("Next steps:")
        print("1. Verify the inventory records: SELECT * FROM inventory;")
        print("2. Run the schema migration: .venv\\Scripts\\alembic.exe upgrade head")
        print("3. Test the API: GET /api/products/{product_id}")
        print()
        
    except Exception as e:
        print(f"✗ Error during migration: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


def verify_migration():
    """Verify the migration by showing inventory records"""
    
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        print("\nInventory Records:")
        print("-" * 70)
        
        inventories = db.query(Inventory).all()
        
        if not inventories:
            print("No inventory records found.")
            return
        
        for inv in inventories:
            product = db.query(Product).get(inv.product_id)
            print(f"ID: {inv.id} | Product: {product.name if product else 'Unknown'} | "
                  f"SKU: {inv.sku or 'N/A'} | Stock: {inv.stock_quantity} | "
                  f"Location: {inv.location or 'N/A'}")
        
        print("-" * 70)
        print(f"Total: {len(inventories)} inventory records")
        
    finally:
        db.close()


if __name__ == "__main__":
    print("\n⚠️  WARNING: This script will migrate variant stock data to inventory table.")
    print("Make sure you have a database backup before proceeding!\n")
    
    response = input("Do you want to continue? (yes/no): ").strip().lower()
    
    if response in ['yes', 'y']:
        try:
            migrate_variant_stock_to_inventory()
            verify_migration()
        except Exception as e:
            print(f"\n✗ Migration failed: {e}")
            sys.exit(1)
    else:
        print("\nMigration cancelled.")
        sys.exit(0)
