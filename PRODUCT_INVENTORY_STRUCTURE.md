# Product & Inventory Response Structure - Fixed

## Problem Solved

**Before:** Inventory was shown at product level with `variant_id` and `variant_name`, creating confusion about which inventory belongs to which variant.

**After:** Inventory is now properly nested under each variant, making the relationship clear.

---

## New Response Structure

### Product Detail Response (`GET /api/products/{id}`)

```json
{
  "id": 6,
  "name": "Nike",
  "description": null,
  "price": "20.00",
  "category_id": 2,
  "category": {
    "id": 2,
    "name": "Shirt"
  },
  "featured": true,
  "status": "active",
  "primary_image": "https://...",
  
  // ✅ NEW: Inventory summary at product level
  "inventory_summary": {
    "total_stock": 150,
    "total_reserved": 0,
    "total_available": 150,
    "low_stock_count": 1
  },
  
  "created_at": "2025-11-28T15:49:34",
  "updated_at": "2025-11-28T15:49:34",
  
  "images": [
    {
      "id": 11,
      "image_url": "https://...",
      "alt_text": "Nike image 1",
      "is_primary": true
    }
  ],
  
  // ✅ NEW: Variants with inventory nested inside
  "variants": [
    {
      "id": 9,
      "product_id": 6,
      "sku": "TS-BUE",
      "variant_name": "Red",
      "color": "Red",
      "size": "M",
      "weight": "0.3",
      "additional_price": "0.00",
      "sort_order": 0,
      
      // Aggregated stock from all inventory locations for this variant
      "stock_quantity": 150,
      "available_quantity": 150,
      
      // ✅ NEW: Inventory details nested under variant
      "inventory": [
        {
          "id": 3,
          "stock_quantity": 100,
          "reserved_quantity": 0,
          "available_quantity": 100,
          "low_stock_threshold": 10,
          "reorder_level": 5,
          "is_low_stock": false,
          "needs_reorder": false,
          "sku": "TS-BUE",
          "batch_number": "BATCH-001",
          "expiry_date": null,
          "location": "Warehouse A",
          "created_at": "2025-11-28T15:49:34",
          "updated_at": "2025-11-28T15:49:34"
        },
        {
          "id": 4,
          "stock_quantity": 50,
          "reserved_quantity": 0,
          "available_quantity": 50,
          "low_stock_threshold": 5,
          "reorder_level": 2,
          "is_low_stock": false,
          "needs_reorder": false,
          "sku": "TS-BUE",
          "batch_number": "BATCH-002",
          "location": "Warehouse B",
          "created_at": "2025-11-28T15:49:34",
          "updated_at": "2025-11-28T15:49:34"
        }
      ],
      
      "created_at": "2025-11-28T15:49:34",
      "updated_at": "2025-11-28T15:49:34"
    },
    {
      "id": 10,
      "product_id": 6,
      "sku": "TS-BUE-m",
      "variant_name": "Blue",
      "color": "Blue",
      "size": "L",
      "weight": "0.35",
      "additional_price": "1.50",
      "sort_order": 1,
      "stock_quantity": 0,
      "available_quantity": 0,
      
      // Empty inventory array = no stock locations
      "inventory": [],
      
      "created_at": "2025-11-28T15:49:34",
      "updated_at": "2025-11-28T15:49:34"
    }
  ]
}
```

---

## Schema Changes

### 1. `InventoryInVariant` (NEW)
Represents inventory records nested within a variant.

```python
class InventoryInVariant(BaseModel):
    id: int
    stock_quantity: int
    reserved_quantity: int
    available_quantity: int
    low_stock_threshold: int
    reorder_level: int
    is_low_stock: bool
    needs_reorder: bool
    sku: Optional[str]
    batch_number: Optional[str]
    expiry_date: Optional[datetime]
    location: Optional[str]
    created_at: datetime
    updated_at: datetime
```

### 2. `ProductVariantResponse` (UPDATED)
Now includes inventory array.

```python
class ProductVariantResponse(ProductVariantBase):
    id: int
    product_id: int
    stock_quantity: int = 0          # Aggregated from all inventory
    available_quantity: int = 0       # Aggregated from all inventory
    inventory: List[InventoryInVariant] = []  # ✅ NEW
    created_at: datetime
    updated_at: datetime
```

### 3. `InventorySimple` (CHANGED)
Now just a summary for product-level view, not individual records.

```python
class InventorySimple(BaseModel):
    total_stock: int = 0
    total_reserved: int = 0
    total_available: int = 0
    low_stock_count: int = 0  # Count of inventory locations with low stock
```

### 4. `ProductResponse` (UPDATED)
Uses inventory_summary instead of inventory list.

```python
class ProductResponse(BaseModel):
    # ... other fields ...
    inventory_summary: Optional[InventorySimple] = None  # ✅ CHANGED from inventory
    # Removed: inventory list
    # Removed: total_stock field
```

---

## Benefits of New Structure

### ✅ Clear Hierarchy
```
Product
├── inventory_summary (aggregated totals)
└── variants[]
    └── inventory[] (detailed records per location)
```

### ✅ No Confusion
- Before: Inventory at product level with variant_id/variant_name was confusing
- After: Inventory is clearly under its parent variant

### ✅ Multi-Location Support
Each variant can have multiple inventory records:
```json
{
  "variant_name": "Red - Medium",
  "inventory": [
    {"location": "Warehouse A", "stock_quantity": 100},
    {"location": "Warehouse B", "stock_quantity": 50}
  ]
}
```

### ✅ Stock Aggregation
Variant-level totals are calculated from all inventory locations:
```
variant.stock_quantity = sum(inv.stock_quantity for inv in variant.inventory)
```

### ✅ Summary at Product Level
Quick overview without drilling into variants:
```json
{
  "inventory_summary": {
    "total_stock": 150,        // All variants, all locations
    "total_available": 145,     // After reserved quantities
    "total_reserved": 5,
    "low_stock_count": 1        // Number of locations with low stock
  }
}
```

---

## Usage Examples

### Get Product with Full Inventory Details
```bash
GET /api/products/6
```

Returns product with:
- Inventory summary
- All variants with their inventory locations

### Check Variant Stock
```javascript
const variant = product.variants.find(v => v.sku === "TS-BUE");
console.log(`Total stock: ${variant.stock_quantity}`);
console.log(`Locations: ${variant.inventory.length}`);
variant.inventory.forEach(inv => {
  console.log(`${inv.location}: ${inv.available_quantity} available`);
});
```

### Find Low Stock Variants
```javascript
const lowStockVariants = product.variants.filter(v => 
  v.inventory.some(inv => inv.is_low_stock)
);
```

### Get All Warehouse Locations
```javascript
const warehouses = new Set();
product.variants.forEach(v => {
  v.inventory.forEach(inv => {
    if (inv.location) warehouses.add(inv.location);
  });
});
```

---

## Comparison: Before vs After

### BEFORE (Confusing) ❌
```json
{
  "id": 6,
  "inventory": [
    {
      "id": 3,
      "variant_id": 9,           // Confusing: why at product level?
      "variant_name": "Red",
      "stock_quantity": 100
    },
    {
      "id": 4,
      "variant_id": 9,           // Duplicate variant info
      "variant_name": "Red",
      "stock_quantity": 50
    }
  ],
  "variants": [
    {
      "id": 9,
      "variant_name": "Red",
      "stock_quantity": 150      // Where is the detailed inventory?
    }
  ]
}
```

### AFTER (Clear) ✅
```json
{
  "id": 6,
  "inventory_summary": {
    "total_stock": 150,
    "total_available": 150
  },
  "variants": [
    {
      "id": 9,
      "variant_name": "Red",
      "stock_quantity": 150,     // Aggregated total
      "inventory": [             // Detailed records
        {
          "id": 3,
          "stock_quantity": 100,
          "location": "Warehouse A"
        },
        {
          "id": 4,
          "stock_quantity": 50,
          "location": "Warehouse B"
        }
      ]
    }
  ]
}
```

---

## Files Changed

1. ✅ `app/schemas/product.py`
   - Added `InventoryInVariant` schema
   - Updated `ProductVariantResponse` to include inventory array
   - Changed `InventorySimple` to summary-only
   - Updated `ProductResponse` to use `inventory_summary`

2. ✅ `app/routers/product_router.py`
   - Updated `transform_variant_with_stock()` to include inventory
   - Updated `transform_product_with_primary_image()` to use inventory_summary
   - Updated `transform_product_with_details()` to nest inventory under variants

---

## Migration Notes

### For Frontend Developers

**Old Code:**
```javascript
// ❌ Old way (no longer works)
product.inventory.forEach(inv => {
  console.log(`${inv.variant_name}: ${inv.stock_quantity}`);
});
```

**New Code:**
```javascript
// ✅ New way
product.variants.forEach(variant => {
  console.log(`${variant.variant_name}: ${variant.stock_quantity}`);
  variant.inventory.forEach(inv => {
    console.log(`  - ${inv.location}: ${inv.stock_quantity}`);
  });
});

// ✅ Or use summary
console.log(`Total: ${product.inventory_summary.total_stock}`);
```

### Database Structure (Unchanged)

The database structure remains the same:
```sql
products (id, name, price, ...)
  ↓
product_variants (id, product_id, sku, variant_name, ...)
  ↓
inventory (id, variant_id, stock_quantity, location, ...)
```

Only the API response structure changed!

---

## Status: ✅ Fixed

The inventory is now properly nested under variants, making the product structure clear and logical.
