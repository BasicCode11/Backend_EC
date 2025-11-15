# Stock Management System - Complete Guide

## Overview

This system implements a **two-level stock management** approach:

1. **Product Inventory** (product-level) = Total available stock
2. **Variant Stock** (variant-level) = Allocated stock per variant

### Key Rules:
✅ **Inventory** = Total stock pool (e.g., 100 units)  
✅ **Variant Stock** ≤ Inventory (e.g., Red=50, Blue=30, Total=80 ≤ 100)  
✅ **When order completes** → Subtract from BOTH variant AND inventory  

---

## System Architecture

```
Product (e.g., "Nike Shoes")
├── Inventory: 100 units (total available)
│   ├── Location: Warehouse A
│   └── Reserved: 5 units (in pending orders)
│
└── Variants
    ├── Red - Medium
    │   └── Stock: 50 units (allocated from inventory)
    └── Blue - Large
        └── Stock: 30 units (allocated from inventory)

Unallocated stock: 100 - 50 - 30 = 20 units
```

---

## How It Works

### 1. Creating Product with Inventory

```bash
POST /api/products

Form Data:
- name: "Nike Shoes"
- price: 99.99
- category_id: 1
- inventory: {
    "stock_quantity": 100,
    "low_stock_threshold": 10,
    "reorder_level": 5,
    "location": "Warehouse A"
  }
```

**Result:**
- Product created with 100 units in inventory
- No variants yet (all 100 units unallocated)

---

### 2. Creating Variants with Stock Allocation

```bash
POST /api/products/8/variants

Form Data:
- variant_name: "Red - Medium"
- sku: "NIKE-RED-M"
- attributes: {"color": "Red", "size": "M"}
- price: 99.99
- stock_quantity: 50  ← Allocate 50 units to this variant
```

**Validation:**
✅ Checks: `50 ≤ 100` (variant stock ≤ inventory) → **PASS**

```bash
POST /api/products/8/variants

Form Data:
- variant_name: "Blue - Large"
- stock_quantity: 30  ← Allocate 30 more units
```

**Validation:**
✅ Checks: `50 + 30 = 80 ≤ 100` (total variants ≤ inventory) → **PASS**

**Now trying to exceed:**
```bash
POST /api/products/8/variants

Form Data:
- variant_name: "Green - Small"
- stock_quantity: 25  ← Would be 80 + 25 = 105
```

**Validation:**
❌ Error: "Total variant stock (105) cannot exceed product inventory (100)"

---

### 3. Order Flow (Stock Reduction)

#### Customer adds to cart:
```json
{
  "product_id": 8,
  "variant_id": 1,  // Red - Medium
  "quantity": 10
}
```

#### Customer checks out:
```bash
POST /api/checkout
```

**What happens:**

1. **Validation:**
   - Check inventory: 100 units available? ✅
   - Check variant: Red-Medium has 50 units? ✅
   - Check requested: 10 ≤ min(100, 50)? ✅

2. **Reserve Stock (during order creation):**
   ```
   Inventory: reserved_quantity += 10  (now 10 reserved)
   ```

3. **Order Fulfillment (when order completes):**
   ```python
   # Reduce from BOTH
   inventory.reserved_quantity -= 10  (release reservation)
   inventory.stock_quantity -= 10     (100 → 90)
   variant.stock_quantity -= 10       (50 → 40)
   ```

**After Order:**
```
Product Inventory: 90 units (was 100)
├── Reserved: 0 units
└── Variants
    ├── Red - Medium: 40 units (was 50)
    └── Blue - Large: 30 units (unchanged)
```

---

## API Endpoints

### Create Product with Inventory

```http
POST /api/products
Content-Type: multipart/form-data

name=Nike Shoes
price=99.99
category_id=1
inventory={"stock_quantity": 100, "location": "Warehouse A"}
```

### Create Variant with Stock

```http
POST /api/products/{product_id}/variants
Content-Type: multipart/form-data

variant_name=Red - Medium
stock_quantity=50
sku=NIKE-RED-M
attributes={"color": "Red", "size": "M"}
```

### Update Variant Stock

```http
PUT /api/products/variants/{variant_id}
Content-Type: multipart/form-data

stock_quantity=60
```

**Validation:** Checks if new total (other variants + 60) ≤ inventory

### Get Product with Stock Info

```http
GET /api/products/{product_id}
```

**Response:**
```json
{
  "id": 8,
  "name": "Nike Shoes",
  "inventory": [
    {
      "id": 1,
      "stock_quantity": 100,
      "reserved_quantity": 5,
      "available_quantity": 95,
      "location": "Warehouse A"
    }
  ],
  "total_stock": 100,
  "variants": [
    {
      "id": 1,
      "variant_name": "Red - Medium",
      "stock_quantity": 50,
      "is_in_stock": true
    },
    {
      "id": 2,
      "variant_name": "Blue - Large",
      "stock_quantity": 30,
      "is_in_stock": true
    }
  ]
}
```

---

## Stock Validation Rules

### Rule 1: Variant Stock ≤ Inventory
```python
sum(all_variant_stocks) ≤ inventory.stock_quantity
```

**Example:**
```
Inventory: 100 units
Variants:
  - Red-M: 50
  - Blue-L: 30
  - Green-S: 15
  
Total: 50 + 30 + 15 = 95 ≤ 100 ✅
```

### Rule 2: Cannot Exceed on Create/Update
When creating/updating a variant, validates:
```python
other_variants_total + new_variant_stock ≤ inventory.stock_quantity
```

### Rule 3: Order Quantity Validation
When ordering, must have enough in BOTH:
```python
quantity ≤ inventory.available_quantity AND
quantity ≤ variant.stock_quantity
```

---

## Error Scenarios

### Error 1: Variant Stock Exceeds Inventory

```http
POST /api/products/8/variants
stock_quantity=150
```

**Response:**
```json
{
  "detail": "No inventory found for product ID 8. Please create inventory before setting variant stock."
}
```

**Solution:** Create inventory first

---

### Error 2: Total Variants Exceed Inventory

```http
PUT /api/products/variants/2
stock_quantity=80
```

With existing Red-M=50, trying to set Blue-L=80:

**Response:**
```json
{
  "detail": "Total variant stock (130) cannot exceed product inventory (100). Other variants: 50, Proposed: 80"
}
```

**Solution:** Reduce stock or increase inventory

---

### Error 3: Insufficient Stock on Order

```http
POST /api/checkout
```

Cart has 60 units of Red-M, but only 50 available:

**Response:**
```json
{
  "detail": "Insufficient variant stock. Available: 50, Requested: 60"
}
```

---

## Stock Consistency Check

```python
from app.services.stock_validation_service import StockValidationService

# Check if product stock is consistent
report = StockValidationService.check_stock_consistency(db, product_id=8)

# Returns:
{
  "product_id": 8,
  "inventory_stock": 100,
  "total_variant_stock": 80,
  "available_unallocated": 20,
  "is_consistent": true,
  "has_inventory": true,
  "variant_count": 2,
  "variants": [
    {"id": 1, "name": "Red - Medium", "stock": 50},
    {"id": 2, "name": "Blue - Large", "stock": 30}
  ]
}
```

---

## Advanced: Stock Synchronization

If variant stocks get out of sync, use:

```python
# Proportional reduction if variants exceed inventory
StockValidationService.sync_variant_stock_to_inventory(
    db=db,
    product_id=8,
    distribute_evenly=False  # Proportional reduction
)

# Or distribute evenly
StockValidationService.sync_variant_stock_to_inventory(
    db=db,
    product_id=8,
    distribute_evenly=True  # Equal distribution
)
```

---

## Complete Order Flow Example

### Step 1: Customer Browses

```http
GET /api/products/8
```

Sees:
- Total stock: 100
- Red-M available: 50
- Blue-L available: 30

### Step 2: Add to Cart

```http
POST /api/cart/items
{
  "product_id": 8,
  "variant_id": 1,
  "quantity": 10
}
```

### Step 3: Checkout

```http
POST /api/checkout
{
  "shipping_address_id": 5
}
```

**Backend Process:**
1. ✅ Validate inventory: 100 ≥ 10
2. ✅ Validate variant: 50 ≥ 10
3. ✅ Reserve: inventory.reserved_quantity = 10
4. ✅ Create order (status=pending)

### Step 4: Payment Complete

Order status changes to "completed"

**Backend Process:**
```python
# Release reservation & reduce stock
inventory.reserved_quantity -= 10  (10 → 0)
inventory.stock_quantity -= 10     (100 → 90)
variant.stock_quantity -= 10       (50 → 40)
```

### Step 5: Verify

```http
GET /api/products/8
```

Returns:
```json
{
  "inventory": [{"stock_quantity": 90, "reserved_quantity": 0}],
  "total_stock": 90,
  "variants": [
    {"variant_name": "Red - Medium", "stock_quantity": 40}
  ]
}
```

---

## Summary

✅ **Inventory** = Product-level total stock  
✅ **Variants** = Sub-allocations from inventory  
✅ **Validation** = Variants cannot exceed inventory  
✅ **Orders** = Reduce from BOTH inventory and variant  
✅ **Reservations** = Temporary holds during checkout  

This system ensures:
- Stock consistency
- Accurate inventory tracking
- Variant-level stock management
- Order fulfillment accuracy
