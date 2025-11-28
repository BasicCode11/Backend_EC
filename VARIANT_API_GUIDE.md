# Product Variant API - Complete Guide

## Overview

The Variant API provides endpoints to manage product variants and their inventory in one place. Each variant can have multiple inventory records (for different locations, batches, etc.).

---

## Architecture

```
Product (e.g., "Nike Shoes")
└── Variants
    ├── Variant 1: Red - Medium
    │   └── Inventory
    │       ├── Warehouse A: 50 units
    │       └── Warehouse B: 30 units
    └── Variant 2: Blue - Large
        └── Inventory
            └── Warehouse A: 40 units
```

### Key Features:
- ✅ **Unified Management**: Create variant + inventory in one request
- ✅ **Flexible Filtering**: Filter by product, search name, low stock
- ✅ **Pagination**: Full pagination support
- ✅ **Cascade Delete**: Deleting variant automatically deletes inventory
- ✅ **Stock Calculation**: Automatic stock aggregation from all inventory locations
- ✅ **Audit Logging**: All operations are logged

---

## Endpoints

### 1. GET /api/variants - List Variants

**Description:** List all product variants with filters and pagination.

**Query Parameters:**
- `product_id` (optional): Filter by product ID
- `search` (optional): Search by variant name (case-insensitive)
- `low_stock` (optional): Filter variants with low stock (true/false)
- `page` (default: 1): Page number
- `limit` (default: 20, max: 100): Items per page
- `sort_by` (default: "sort_order"): Sort field (variant_name, sku, sort_order, created_at, updated_at)
- `sort_order` (default: "asc"): Sort direction (asc/desc)

**Example Request:**
```bash
GET /api/variants?product_id=1&search=red&page=1&limit=20
Authorization: Bearer YOUR_TOKEN
```

**Example Response:**
```json
{
  "items": [
    {
      "id": 1,
      "product_id": 1,
      "sku": "PROD-RED-M",
      "variant_name": "Red - Medium",
      "color": "Red",
      "size": "M",
      "weight": "1.2kg",
      "additional_price": 5.00,
      "sort_order": 0,
      "product": {
        "id": 1,
        "name": "Nike Shoes",
        "price": 99.99
      },
      "stock_quantity": 80,
      "available_quantity": 75,
      "is_low_stock": false,
      "inventory": [
        {
          "id": 1,
          "stock_quantity": 50,
          "reserved_quantity": 5,
          "available_quantity": 45,
          "low_stock_threshold": 10,
          "reorder_level": 5,
          "is_low_stock": false,
          "needs_reorder": false,
          "sku": "PROD-RED-M",
          "batch_number": "BATCH-001",
          "location": "Warehouse A",
          "created_at": "2025-01-15T10:30:00Z",
          "updated_at": "2025-01-15T10:30:00Z"
        },
        {
          "id": 2,
          "stock_quantity": 30,
          "reserved_quantity": 0,
          "available_quantity": 30,
          "low_stock_threshold": 10,
          "reorder_level": 5,
          "is_low_stock": false,
          "needs_reorder": false,
          "location": "Warehouse B",
          "created_at": "2025-01-15T10:30:00Z",
          "updated_at": "2025-01-15T10:30:00Z"
        }
      ],
      "created_at": "2025-01-15T10:30:00Z",
      "updated_at": "2025-01-15T10:30:00Z"
    }
  ],
  "total": 25,
  "page": 1,
  "limit": 20,
  "pages": 2
}
```

**Use Cases:**
- List all variants for a specific product
- Search for variants by name
- Find variants with low stock
- Paginate through large variant lists

---

### 2. POST /api/variants - Create Variant with Inventory

**Description:** Create a new product variant with one or more inventory records.

**Request Body:**
```json
{
  "product_id": 1,
  "sku": "PROD-RED-M",
  "variant_name": "Red - Medium",
  "color": "Red",
  "size": "M",
  "weight": "1.2kg",
  "additional_price": 5.00,
  "sort_order": 0,
  "inventory": [
    {
      "stock_quantity": 100,
      "reserved_quantity": 0,
      "low_stock_threshold": 10,
      "reorder_level": 5,
      "sku": "PROD-RED-M",
      "batch_number": "BATCH-001",
      "expiry_date": "2025-12-31T00:00:00Z",
      "location": "Warehouse A"
    },
    {
      "stock_quantity": 50,
      "reserved_quantity": 0,
      "low_stock_threshold": 5,
      "reorder_level": 3,
      "sku": "PROD-RED-M-B",
      "batch_number": "BATCH-002",
      "location": "Warehouse B"
    }
  ]
}
```

**Example Request:**
```bash
POST /api/variants
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "product_id": 1,
  "variant_name": "Red - Medium",
  "sku": "PROD-RED-M",
  "color": "Red",
  "size": "M",
  "inventory": [
    {
      "stock_quantity": 100,
      "location": "Warehouse A"
    }
  ]
}
```

**Example Response:**
```json
{
  "id": 1,
  "product_id": 1,
  "sku": "PROD-RED-M",
  "variant_name": "Red - Medium",
  "color": "Red",
  "size": "M",
  "weight": null,
  "additional_price": null,
  "sort_order": 0,
  "product": {
    "id": 1,
    "name": "Nike Shoes",
    "price": 99.99
  },
  "stock_quantity": 100,
  "available_quantity": 100,
  "is_low_stock": false,
  "inventory": [
    {
      "id": 1,
      "stock_quantity": 100,
      "reserved_quantity": 0,
      "available_quantity": 100,
      "low_stock_threshold": 10,
      "reorder_level": 5,
      "is_low_stock": false,
      "needs_reorder": false,
      "location": "Warehouse A",
      "created_at": "2025-01-15T10:30:00Z",
      "updated_at": "2025-01-15T10:30:00Z"
    }
  ],
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

**Notes:**
- SKU must be unique across all variants
- Inventory array is optional but recommended
- You can create multiple inventory records for different locations
- Stock quantities are automatically calculated from all inventory records

---

### 3. PUT /api/variants/{variant_id} - Update Variant with Inventory

**Description:** Update a variant and its inventory. All fields are optional.

**Request Body:**
```json
{
  "variant_name": "Red - Large",
  "size": "L",
  "additional_price": 7.50,
  "sort_order": 1,
  "inventory": [
    {
      "stock_quantity": 150,
      "low_stock_threshold": 15,
      "location": "Warehouse A"
    }
  ]
}
```

**Example Request:**
```bash
PUT /api/variants/1
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "variant_name": "Red - Large",
  "size": "L",
  "inventory": [
    {
      "stock_quantity": 150
    }
  ]
}
```

**Example Response:**
```json
{
  "id": 1,
  "product_id": 1,
  "sku": "PROD-RED-M",
  "variant_name": "Red - Large",
  "color": "Red",
  "size": "L",
  "weight": "1.2kg",
  "additional_price": 7.50,
  "sort_order": 1,
  "product": {
    "id": 1,
    "name": "Nike Shoes",
    "price": 99.99
  },
  "stock_quantity": 150,
  "available_quantity": 145,
  "is_low_stock": false,
  "inventory": [
    {
      "id": 1,
      "stock_quantity": 150,
      "reserved_quantity": 5,
      "available_quantity": 145,
      "location": "Warehouse A",
      "updated_at": "2025-01-16T14:20:00Z"
    }
  ],
  "updated_at": "2025-01-16T14:20:00Z"
}
```

**Update Behavior:**
- Updates existing inventory records by index
- If more inventory data is provided than exists, creates new records
- Only updates fields that are provided (partial update)

---

### 4. DELETE /api/variants/{variant_id} - Delete Variant and Inventory

**Description:** Delete a variant and all its inventory records (cascade delete).

**Example Request:**
```bash
DELETE /api/variants/1
Authorization: Bearer YOUR_TOKEN
```

**Example Response:**
```json
{
  "message": "Variant deleted successfully",
  "deleted_inventory_count": 2
}
```

**Restrictions:**
- ❌ Cannot delete variants in existing orders
- ❌ Cannot delete variants in shopping carts
- ✅ Inventory is automatically deleted (CASCADE)

---

## Bonus Endpoints

### 5. GET /api/variants/{variant_id} - Get Single Variant

**Description:** Get detailed information about a single variant.

**Example Request:**
```bash
GET /api/variants/1
Authorization: Bearer YOUR_TOKEN
```

**Response:** Same format as list endpoint item.

---

### 6. GET /api/variants/stats/count - Get Variant Count

**Description:** Get total count of variants with optional product filter.

**Example Request:**
```bash
GET /api/variants/stats/count?product_id=1
Authorization: Bearer YOUR_TOKEN
```

**Example Response:**
```json
{
  "count": 25,
  "product_id": 1
}
```

---

## Complete Workflow Example

### Step 1: Create a Product Variant with Inventory

```bash
curl -X POST http://localhost:8000/api/variants \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": 1,
    "sku": "NIKE-RED-M",
    "variant_name": "Red - Medium",
    "color": "Red",
    "size": "M",
    "weight": "1.2kg",
    "additional_price": 5.00,
    "sort_order": 0,
    "inventory": [
      {
        "stock_quantity": 100,
        "reserved_quantity": 0,
        "low_stock_threshold": 10,
        "reorder_level": 5,
        "sku": "NIKE-RED-M",
        "batch_number": "BATCH-2025-001",
        "location": "Warehouse A"
      }
    ]
  }'
```

### Step 2: List All Variants for Product

```bash
curl -X GET "http://localhost:8000/api/variants?product_id=1&page=1&limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Step 3: Search for Low Stock Variants

```bash
curl -X GET "http://localhost:8000/api/variants?low_stock=true&page=1&limit=20" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Step 4: Update Variant Stock

```bash
curl -X PUT http://localhost:8000/api/variants/1 \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "inventory": [
      {
        "stock_quantity": 150,
        "low_stock_threshold": 15
      }
    ]
  }'
```

### Step 5: Delete Variant

```bash
curl -X DELETE http://localhost:8000/api/variants/1 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "SKU 'PROD-RED-M' already exists"
}
```

### 404 Not Found
```json
{
  "detail": "Variant with ID 999 not found"
}
```

### 400 Bad Request (Delete Constraint)
```json
{
  "detail": "Cannot delete variant with existing orders"
}
```

---

## Permissions Required

All endpoints require authentication and specific permissions:

- **GET /api/variants**: `products:read`
- **POST /api/variants**: `products:create`
- **PUT /api/variants/{variant_id}**: `products:update`
- **DELETE /api/variants/{variant_id}**: `products:delete`
- **GET /api/variants/{variant_id}**: `products:read`
- **GET /api/variants/stats/count**: `products:read`

---

## Key Features Summary

✅ **Unified Operations**: Manage variant + inventory in one request  
✅ **Flexible Filtering**: Product, search, low stock filters  
✅ **Pagination**: Full pagination support  
✅ **Multi-Location**: Support multiple inventory locations per variant  
✅ **Automatic Calculations**: Stock totals, available quantity, low stock detection  
✅ **Cascade Delete**: Delete variant → inventory auto-deleted  
✅ **Audit Logging**: All operations logged for compliance  
✅ **SKU Uniqueness**: Automatic SKU validation  
✅ **Order Protection**: Cannot delete variants in orders/carts  

---

## Database Schema

```sql
-- ProductVariant Table
CREATE TABLE product_variants (
    id INTEGER PRIMARY KEY,
    product_id INTEGER NOT NULL,
    sku VARCHAR(100) UNIQUE,
    variant_name VARCHAR(255) NOT NULL,
    color VARCHAR(50),
    size VARCHAR(50),
    weight VARCHAR(20),
    additional_price DECIMAL(10, 2),
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT
);

-- Inventory Table
CREATE TABLE inventory (
    id INTEGER PRIMARY KEY,
    variant_id INTEGER NOT NULL,
    stock_quantity INTEGER DEFAULT 0,
    reserved_quantity INTEGER DEFAULT 0,
    low_stock_threshold INTEGER DEFAULT 10,
    reorder_level INTEGER DEFAULT 5,
    sku VARCHAR(100),
    batch_number VARCHAR(100),
    expiry_date TIMESTAMP,
    location VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (variant_id) REFERENCES product_variants(id) ON DELETE CASCADE
);
```

**Note:** Inventory has `ON DELETE CASCADE` - when variant is deleted, inventory is automatically deleted.

---

## Status: ✅ Complete

All 4 required endpoints are fully implemented and documented!

**Created Files:**
1. ✅ `app/schemas/variant.py` - Variant and inventory schemas
2. ✅ `app/services/variant_service.py` - Business logic
3. ✅ `app/routers/variant_router.py` - API endpoints
4. ✅ `app/main.py` - Router registration

**Ready to Use!**
