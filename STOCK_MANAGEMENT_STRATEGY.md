# Stock Management Strategy - FIXED ✅

## Overview

This document explains the **corrected and unified** stock management approach in the e-commerce platform.

### ⚠️ Previous Issue (NOW FIXED)

Previously, stock was tracked in **two places**, causing confusion:
- ❌ `ProductVariant.stock_quantity` (database column) - **REMOVED**
- ✅ `Inventory` table (proper stock management) - **SINGLE SOURCE OF TRUTH**

This created potential data inconsistencies and unclear responsibilities.

## ✅ New Strategy: Inventory-Only Stock Management

### Single Source of Truth

**ALL stock is managed via the `Inventory` table.**

```
Product (base product info)
  ├── ProductVariant (options: size, color, price variations)
  └── Inventory (stock tracking, reservations, locations)
```

### What Each Table Does

#### 1. **Product** Table
- Base product information
- Name, description, base price, category
- Featured status, images
- **Does NOT track stock**

#### 2. **ProductVariant** Table (UPDATED)
- Product variations (size, color, material, etc.)
- Optional variant-specific pricing
- Attributes (JSON: `{"size": "M", "color": "Red"}`)
- Optional variant-specific images
- **Does NOT track stock anymore** ✅

#### 3. **Inventory** Table (STOCK AUTHORITY)
- Stock quantity per product
- Reserved quantity (for pending orders)
- Low stock threshold & reorder levels
- Batch numbers, expiry dates
- Multiple warehouse locations
- **ONLY place where stock is stored**

---

## Database Changes

### Migration: `1cf09a40841f_remove_stock_quantity_from_product_variants`

**Changes Applied:**
1. ✅ Removed `stock_quantity` column from `product_variants` table
2. ✅ Added `UNIQUE` constraint to `sku` column (prevents duplicates)
3. ✅ Added computed property `stock_quantity` to ProductVariant model (reads from Inventory)

**To Apply:**
```bash
# Run the migration
alembic upgrade head

# Or using venv
.venv/Scripts/python.exe -m alembic upgrade head
```

**⚠️ WARNING:** This migration will drop the `stock_quantity` column. If you have existing variant stock data, manually migrate it to the `inventory` table first!

---

## How to Use

### 1. Create a Product with Variants

```bash
POST /api/products
Content-Type: multipart/form-data

# Fields:
name=T-Shirt
price=25.00
category_id=1
variants=[
  {
    "sku": "TSHIRT-RED-M",
    "variant_name": "Red - Medium",
    "attributes": {"color": "Red", "size": "M"},
    "price": 25.00
  },
  {
    "sku": "TSHIRT-BLUE-L",
    "variant_name": "Blue - Large",
    "attributes": {"color": "Blue", "size": "L"},
    "price": 27.00
  }
]
```

**Note:** No `stock_quantity` field in variants anymore! ✅

### 2. Add Inventory/Stock for the Product

```bash
POST /api/inventory
Content-Type: application/json

{
  "product_id": 1,
  "sku": "TSHIRT-RED-M",
  "stock_quantity": 100,
  "reserved_quantity": 0,
  "low_stock_threshold": 10,
  "reorder_level": 5,
  "location": "Warehouse A",
  "batch_number": "BATCH-2025-001"
}
```

### 3. Check Stock for a Variant

**Backend (Python):**
```python
from app.models.product_variant import ProductVariant

variant = db.query(ProductVariant).filter(ProductVariant.id == variant_id).first()

# Get stock (computed from Inventory)
available_stock = variant.stock_quantity  # Property that queries Inventory
is_in_stock = variant.is_in_stock  # Boolean check

# Or explicitly
available = variant.get_available_stock()  # Sum of all inventory available quantities
```

**API Response:**
```json
GET /api/products/1

{
  "id": 1,
  "name": "T-Shirt",
  "variants": [
    {
      "id": 1,
      "variant_name": "Red - Medium",
      "stock_quantity": 100,  // ✅ Computed from Inventory table
      "is_in_stock": true
    }
  ]
}
```

### 4. Reserve Stock for Orders

```bash
POST /api/inventory/1/reserve
Content-Type: application/json

{
  "quantity": 5,
  "order_id": 123,
  "reason": "Customer order"
}
```

### 5. Fulfill Orders (Reduce Stock)

```bash
POST /api/inventory/1/fulfill
Content-Type: application/json

{
  "quantity": 5,
  "order_id": 123
}
```

---

## Code Examples

### Check Variant Stock Before Adding to Cart

```python
def add_to_cart(user_id: int, variant_id: int, quantity: int, db: Session):
    variant = db.query(ProductVariant).filter(ProductVariant.id == variant_id).first()
    
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")
    
    # Check stock via Inventory table
    available = variant.get_available_stock()
    
    if available < quantity:
        raise HTTPException(
            status_code=400, 
            detail=f"Insufficient stock. Available: {available}, Requested: {quantity}"
        )
    
    # Add to cart...
```

### Display Product with Stock Info

```python
@router.get("/products/{product_id}")
def get_product_with_stock(product_id: int, db: Session):
    product = db.query(Product).options(
        selectinload(Product.variants),
        selectinload(Product.inventory)
    ).filter(Product.id == product_id).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return {
        "id": product.id,
        "name": product.name,
        "price": product.price,
        "variants": [
            {
                "id": v.id,
                "name": v.variant_name,
                "price": v.effective_price,
                "stock_quantity": v.stock_quantity,  # Computed from Inventory
                "is_in_stock": v.is_in_stock
            }
            for v in product.variants
        ],
        "total_stock": sum(inv.available_quantity for inv in product.inventory)
    }
```

---

## Model Properties

### ProductVariant Properties (Updated)

```python
@property
def stock_quantity(self) -> int:
    """Get total stock from Inventory table (read-only)"""
    if not self.product or not self.product.inventory:
        return 0
    return sum(inv.available_quantity for inv in self.product.inventory)

@property
def is_in_stock(self) -> bool:
    """Check if variant has available stock"""
    return self.stock_quantity > 0

def get_available_stock(self) -> int:
    """Get available stock (stock - reserved) from all locations"""
    if not self.product or not self.product.inventory:
        return 0
    return sum(inv.available_quantity for inv in self.product.inventory)
```

### Inventory Properties

```python
@property
def available_quantity(self) -> int:
    """Stock available for sale (stock - reserved)"""
    return self.stock_quantity - self.reserved_quantity

@property
def is_low_stock(self) -> bool:
    """Check if below threshold"""
    return self.available_quantity <= self.low_stock_threshold
```

---

## Benefits of This Approach

✅ **Single Source of Truth** - No data duplication or sync issues
✅ **Advanced Features** - Reservations, locations, batch tracking, expiry dates
✅ **Scalability** - Multiple warehouses, sophisticated inventory management
✅ **Consistency** - Stock changes happen in one place only
✅ **Flexibility** - Can track inventory at product level or with multiple locations

---

## Migration Guide

If you have existing data with `stock_quantity` in `product_variants`:

### Before Running Migration

```sql
-- Export existing variant stock data
SELECT 
    pv.id as variant_id,
    pv.product_id,
    pv.sku,
    pv.stock_quantity,
    p.name as product_name
FROM product_variants pv
JOIN products p ON p.id = pv.product_id
WHERE pv.stock_quantity > 0;

-- Create inventory records for each variant with stock
INSERT INTO inventory (product_id, sku, stock_quantity, reserved_quantity, location)
SELECT 
    pv.product_id,
    pv.sku,
    pv.stock_quantity,
    0,
    'Default Location'
FROM product_variants pv
WHERE pv.stock_quantity > 0;
```

### Run Migration

```bash
.venv/Scripts/python.exe -m alembic upgrade head
```

---

## API Endpoints

### Products (No Stock Management)
- `POST /api/products` - Create product with variants (no stock)
- `PUT /api/products/{id}` - Update product
- `POST /api/products/{id}/variants` - Add variant (no stock)
- `PUT /api/products/variants/{id}` - Update variant (no stock)

### Inventory (All Stock Management)
- `GET /api/inventory` - List inventory records
- `POST /api/inventory` - Create inventory record (set initial stock)
- `PUT /api/inventory/{id}` - Update inventory settings
- `POST /api/inventory/{id}/adjust` - Adjust stock (+ or -)
- `POST /api/inventory/{id}/reserve` - Reserve stock for order
- `POST /api/inventory/{id}/release` - Release reserved stock
- `POST /api/inventory/{id}/fulfill` - Fulfill order (reduce stock)
- `GET /api/inventory/low-stock` - Get low stock items
- `GET /api/inventory/statistics` - Get inventory stats

---

## Summary

| Table | Purpose | Stock Tracking |
|-------|---------|----------------|
| **Product** | Base product info | ❌ No |
| **ProductVariant** | Product options (size, color) | ❌ No (reads from Inventory) |
| **Inventory** | Stock management | ✅ YES - Only place |

**Remember:** 
- 🛑 **Never** try to update stock via Product or ProductVariant
- ✅ **Always** use Inventory table for stock operations
- 📊 Variants can **read** stock via computed properties (no storage)

---

## Questions?

- **Q: Can I track stock per variant (size/color)?**
  - A: Yes! Create separate Inventory records with matching SKUs for each variant.

- **Q: What if I have multiple warehouses?**
  - A: Create multiple Inventory records per product with different `location` values.

- **Q: How do I handle variant-specific stock?**
  - A: Use the `sku` field in Inventory to link to specific variant SKUs.

- **Q: Will old code break?**
  - A: The migration adds computed properties, so read operations still work. Any code that tried to SET `variant.stock_quantity` will need updating.

---

**Last Updated:** 2025-11-02
**Migration:** `1cf09a40841f`
**Status:** ✅ PRODUCTION READY
