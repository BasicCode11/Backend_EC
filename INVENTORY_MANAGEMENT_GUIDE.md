# Inventory Management System Guide

## Overview
This comprehensive inventory management system provides complete control over product stock, including real-time tracking, reservations, adjustments, transfers, and automated alerts for low stock and reorder levels.

## Features

### Core Functionality
- ✅ **Stock Management**: Track stock quantities, reserved stock, and available stock
- ✅ **Inventory Adjustments**: Add or reduce stock with reason tracking
- ✅ **Stock Reservations**: Reserve stock for orders before fulfillment
- ✅ **Order Fulfillment**: Complete orders by reducing both reserved and actual stock
- ✅ **Stock Transfers**: Move inventory between locations/warehouses
- ✅ **Low Stock Alerts**: Automatic detection of low stock items
- ✅ **Reorder Management**: Track items that need reordering
- ✅ **Expiry Tracking**: Monitor expired inventory items
- ✅ **Batch Management**: Track inventory by batch numbers
- ✅ **Location Management**: Organize inventory by warehouse/location
- ✅ **SKU Management**: Unique SKU tracking for each inventory item
- ✅ **Statistics Dashboard**: Real-time inventory statistics and metrics
- ✅ **Audit Logging**: All inventory operations are logged for audit trails

### Advanced Features
- Multi-location inventory support
- Automatic calculation of available quantity (stock - reserved)
- Low stock threshold monitoring
- Reorder level tracking
- Expiry date management
- Batch number tracking
- Comprehensive search and filtering

## Database Model

### Inventory Table Structure
```python
class Inventory(Base):
    id: int                          # Primary key
    product_id: int                  # Foreign key to products table
    stock_quantity: int              # Total stock quantity
    reserved_quantity: int           # Quantity reserved for orders
    low_stock_threshold: int         # Alert threshold for low stock
    reorder_level: int               # Threshold to trigger reorder
    sku: str (optional)              # Stock Keeping Unit
    batch_number: str (optional)     # Batch/lot number
    expiry_date: datetime (optional) # Product expiry date
    location: str (optional)         # Warehouse/storage location
    created_at: datetime             # Creation timestamp
    updated_at: datetime             # Last update timestamp
```

### Computed Properties
- **available_quantity**: `stock_quantity - reserved_quantity`
- **is_low_stock**: `available_quantity <= low_stock_threshold`
- **needs_reorder**: `available_quantity <= reorder_level`
- **is_expired**: `expiry_date < current_datetime`

## API Endpoints

### 1. Get All Inventory
```http
GET /api/inventory?product_id={id}&location={location}&page=1&limit=20
```
**Description**: Retrieve all inventory records with pagination and filters

**Query Parameters**:
- `product_id` (optional): Filter by product ID
- `location` (optional): Filter by location
- `page` (default: 1): Page number
- `limit` (default: 20): Items per page

**Response**: Paginated list of inventory items

---

### 2. Search Inventory (Advanced)
```http
POST /api/inventory/search
Content-Type: application/json

{
  "search": "search term",
  "product_id": 1,
  "location": "Warehouse A",
  "low_stock": true,
  "needs_reorder": false,
  "expired": false,
  "min_stock": 10,
  "max_stock": 1000,
  "page": 1,
  "limit": 20,
  "sort_by": "stock_quantity",
  "sort_order": "desc"
}
```
**Description**: Advanced search with multiple filters

**Request Body Fields**:
- `search`: Search in product name, SKU, batch number, location
- `product_id`: Filter by specific product
- `location`: Filter by location (partial match)
- `low_stock`: Show only low stock items
- `needs_reorder`: Show only items needing reorder
- `expired`: Show only expired items
- `min_stock`, `max_stock`: Stock quantity range
- `sort_by`: Field to sort by (stock_quantity, available_quantity, created_at, updated_at)
- `sort_order`: asc or desc

---

### 3. Get Inventory Statistics
```http
GET /api/inventory/statistics
```
**Description**: Get comprehensive inventory statistics

**Response**:
```json
{
  "total_products": 150,
  "total_stock": 5000,
  "total_reserved": 250,
  "total_available": 4750,
  "low_stock_count": 12,
  "needs_reorder_count": 5,
  "expired_count": 3,
  "out_of_stock_count": 8
}
```

---

### 4. Get Low Stock Items
```http
GET /api/inventory/low-stock
```
**Description**: Get all items with stock below low_stock_threshold

---

### 5. Get Items Needing Reorder
```http
GET /api/inventory/reorder
```
**Description**: Get all items with stock below reorder_level

---

### 6. Get Expired Items
```http
GET /api/inventory/expired
```
**Description**: Get all items past their expiry date

---

### 7. Get Inventory by ID
```http
GET /api/inventory/{inventory_id}
```
**Description**: Get specific inventory record by ID

---

### 8. Get Inventory by Product
```http
GET /api/inventory/product/{product_id}
```
**Description**: Get all inventory records for a specific product (useful for multi-location)

---

### 9. Get Inventory by SKU
```http
GET /api/inventory/sku/{sku}
```
**Description**: Get inventory by unique SKU

---

### 10. Create Inventory
```http
POST /api/inventory
Content-Type: application/json
Authorization: Bearer {token}

{
  "product_id": 1,
  "stock_quantity": 100,
  "reserved_quantity": 0,
  "low_stock_threshold": 10,
  "reorder_level": 5,
  "sku": "PROD-001-WH-A",
  "batch_number": "BATCH-2025-001",
  "expiry_date": "2025-12-31T00:00:00Z",
  "location": "Warehouse A"
}
```
**Permission Required**: `create:inventory`

**Description**: Create new inventory record for a product

---

### 11. Update Inventory
```http
PUT /api/inventory/{inventory_id}
Content-Type: application/json
Authorization: Bearer {token}

{
  "stock_quantity": 150,
  "low_stock_threshold": 15,
  "reorder_level": 8,
  "location": "Warehouse B"
}
```
**Permission Required**: `update:inventory`

**Description**: Update existing inventory record (all fields optional)

---

### 12. Delete Inventory
```http
DELETE /api/inventory/{inventory_id}
Authorization: Bearer {token}
```
**Permission Required**: `delete:inventory`

**Description**: Delete inventory record (only if no reserved stock)

**Note**: Cannot delete if `reserved_quantity > 0`

---

### 13. Adjust Stock
```http
POST /api/inventory/{inventory_id}/adjust
Content-Type: application/json
Authorization: Bearer {token}

{
  "quantity": 50,
  "reason": "Received new shipment"
}
```
**Permission Required**: `adjust:inventory`

**Description**: Adjust inventory stock (positive to add, negative to reduce)

**Examples**:
- Add stock: `{"quantity": 50, "reason": "New shipment"}`
- Reduce stock: `{"quantity": -10, "reason": "Damaged items"}`

**Validations**:
- Cannot reduce stock below 0
- Cannot reduce stock below reserved quantity

---

### 14. Reserve Stock
```http
POST /api/inventory/{inventory_id}/reserve
Content-Type: application/json
Authorization: Bearer {token}

{
  "quantity": 5,
  "order_id": 123
}
```
**Permission Required**: `reserve:inventory`

**Description**: Reserve stock for an order (increases reserved_quantity)

**Use Case**: When a customer places an order, reserve the items to prevent overselling

**Validations**:
- Sufficient available stock must exist
- `available_quantity >= quantity`

---

### 15. Release Stock
```http
POST /api/inventory/{inventory_id}/release
Content-Type: application/json
Authorization: Bearer {token}

{
  "quantity": 5,
  "order_id": 123
}
```
**Permission Required**: `release:inventory`

**Description**: Release previously reserved stock (decreases reserved_quantity)

**Use Case**: When an order is cancelled, release the reserved items back to available stock

**Validations**:
- Cannot release more than reserved
- `reserved_quantity >= quantity`

---

### 16. Fulfill Order
```http
POST /api/inventory/{inventory_id}/fulfill?quantity=5&order_id=123
Authorization: Bearer {token}
```
**Permission Required**: `fulfill:inventory`

**Description**: Complete order fulfillment (reduces both reserved_quantity and stock_quantity)

**Use Case**: When an order is shipped/completed, actually remove the items from inventory

**Process**:
1. Reduces `reserved_quantity` by the amount
2. Reduces `stock_quantity` by the amount
3. Logs the fulfillment action

**Validations**:
- Sufficient reserved stock must exist
- `reserved_quantity >= quantity`

---

### 17. Transfer Stock
```http
POST /api/inventory/transfer
Content-Type: application/json
Authorization: Bearer {token}

{
  "from_inventory_id": 1,
  "to_inventory_id": 2,
  "quantity": 20,
  "reason": "Rebalancing warehouse stock"
}
```
**Permission Required**: `transfer:inventory`

**Description**: Transfer stock between two inventory locations

**Use Case**: Move inventory from one warehouse to another

**Validations**:
- Both inventory records must exist
- Must be for the same product
- Sufficient available stock in source location
- `source.available_quantity >= quantity`

**Process**:
1. Reduces stock in source inventory
2. Increases stock in destination inventory
3. Logs the transfer with reason

---

## Inventory Workflow Examples

### Example 1: New Product Arrival
```bash
# 1. Create inventory for new product
POST /api/inventory
{
  "product_id": 10,
  "stock_quantity": 500,
  "reserved_quantity": 0,
  "low_stock_threshold": 50,
  "reorder_level": 20,
  "sku": "PHONE-X-001",
  "batch_number": "2025-Q1-001",
  "location": "Main Warehouse"
}
```

### Example 2: Order Processing Flow
```bash
# Step 1: Customer places order - Reserve stock
POST /api/inventory/15/reserve
{
  "quantity": 3,
  "order_id": 456
}

# Step 2: Order is shipped - Fulfill order
POST /api/inventory/15/fulfill?quantity=3&order_id=456

# Alternative: Order cancelled - Release stock
POST /api/inventory/15/release
{
  "quantity": 3,
  "order_id": 456
}
```

### Example 3: Stock Adjustment
```bash
# Damaged items found during inspection
POST /api/inventory/20/adjust
{
  "quantity": -5,
  "reason": "Damaged during inspection - discarded"
}

# Received return from customer
POST /api/inventory/20/adjust
{
  "quantity": 2,
  "reason": "Customer return - items in good condition"
}
```

### Example 4: Warehouse Transfer
```bash
# Transfer 100 units from Main Warehouse to Regional Warehouse
POST /api/inventory/transfer
{
  "from_inventory_id": 10,
  "to_inventory_id": 25,
  "quantity": 100,
  "reason": "Seasonal demand in Region B"
}
```

### Example 5: Low Stock Monitoring
```bash
# Check all low stock items
GET /api/inventory/low-stock

# Check items needing reorder
GET /api/inventory/reorder

# Get inventory statistics
GET /api/inventory/statistics
```

## Required Permissions

To use the inventory system, users need the following permissions:

| Permission | Description |
|------------|-------------|
| `create:inventory` | Create new inventory records |
| `update:inventory` | Update existing inventory records |
| `delete:inventory` | Delete inventory records |
| `adjust:inventory` | Adjust stock quantities |
| `reserve:inventory` | Reserve stock for orders |
| `release:inventory` | Release reserved stock |
| `fulfill:inventory` | Fulfill orders (complete stock reduction) |
| `transfer:inventory` | Transfer stock between locations |

**Note**: All read operations (GET endpoints) only require authentication, no special permissions needed.

## Audit Logging

All inventory operations are automatically logged with the following information:
- User who performed the action
- Action type (CREATE, UPDATE, DELETE, STOCK_INCREASE, STOCK_DECREASE, STOCK_RESERVED, STOCK_RELEASED, ORDER_FULFILLED, STOCK_TRANSFER)
- Resource type (Inventory)
- Resource ID
- Detailed description of the change
- Timestamp

## Best Practices

### 1. Stock Reservation
- Always reserve stock when an order is placed
- Release stock if order is cancelled within a reasonable timeframe
- Implement automatic cleanup for expired reservations

### 2. Low Stock Management
- Set appropriate `low_stock_threshold` based on product demand
- Set `reorder_level` lower than `low_stock_threshold`
- Regularly check `/api/inventory/reorder` endpoint

### 3. Multi-Location Inventory
- Create separate inventory records for each location
- Use descriptive location names
- Include location in SKU for easier tracking

### 4. Batch Management
- Always include batch numbers for products with expiry dates
- Use consistent batch number format
- Regularly check `/api/inventory/expired` endpoint

### 5. Stock Adjustments
- Always provide a clear reason for adjustments
- Use positive numbers for additions, negative for reductions
- Audit adjustment logs regularly for discrepancies

### 6. Order Fulfillment Process
```
Order Placed → Reserve Stock → Payment Confirmed → Fulfill Order
              ↓ (if cancelled)
              Release Stock
```

## Error Handling

Common errors and their solutions:

### 1. Insufficient Stock
```json
{
  "detail": "Insufficient available stock. Available: 5, Requested: 10"
}
```
**Solution**: Reduce order quantity or wait for restocking

### 2. Cannot Delete with Reserved Stock
```json
{
  "detail": "Cannot delete inventory with reserved quantity (5 units reserved)"
}
```
**Solution**: Release all reserved stock before deletion

### 3. Transfer Between Different Products
```json
{
  "detail": "Cannot transfer stock between different products"
}
```
**Solution**: Ensure both inventory records belong to the same product

### 4. Duplicate SKU
```json
{
  "detail": "Inventory with SKU PROD-001 already exists"
}
```
**Solution**: Use a unique SKU or update existing inventory record

## Database Relationships

```
Product (1) ← → (Many) Inventory
                         ↓
                    (tracks stock at different locations/batches)
```

Each product can have multiple inventory records for:
- Different warehouse locations
- Different batches
- Different expiry dates

## Integration with Orders

The inventory system integrates with order management:

1. **Order Creation**: Reserve stock
2. **Order Payment**: Confirm reservation
3. **Order Shipment**: Fulfill order (reduce stock)
4. **Order Cancellation**: Release reserved stock

## Monitoring and Analytics

### Key Metrics to Track
1. **Total Stock Value**: Sum of (stock_quantity × product_price)
2. **Turnover Rate**: How fast inventory is sold
3. **Low Stock Frequency**: How often items fall below threshold
4. **Out of Stock Incidents**: Track when available_quantity = 0
5. **Expiry Rate**: Percentage of items expiring before sale

### Dashboard Queries
```python
# Get statistics
GET /api/inventory/statistics

# Monitor critical items
GET /api/inventory/low-stock
GET /api/inventory/reorder
GET /api/inventory/expired

# Search specific conditions
POST /api/inventory/search
{
  "low_stock": true,
  "sort_by": "available_quantity",
  "sort_order": "asc"
}
```

## Future Enhancements

Potential features for future versions:
- [ ] Automatic reorder system
- [ ] Supplier integration
- [ ] Barcode scanning support
- [ ] Inventory forecasting
- [ ] FIFO/LIFO inventory methods
- [ ] Cost tracking per batch
- [ ] Automated expiry notifications
- [ ] Multi-currency support
- [ ] Import/Export functionality
- [ ] Advanced reporting and analytics

## Troubleshooting

### Problem: Stock count doesn't match reality
**Solution**: Use the adjust endpoint with detailed reason to correct discrepancies

### Problem: Reserved quantity is stuck
**Solution**: Identify associated orders and manually release if orders are cancelled/expired

### Problem: Low stock alerts not triggering
**Solution**: Check and adjust `low_stock_threshold` values for products

### Problem: Cannot fulfill order
**Solution**: Ensure stock was reserved first, and sufficient reserved quantity exists

## Support

For issues or questions:
1. Check the audit logs: `GET /api/audit-logs?resource_type=Inventory`
2. Review inventory statistics for anomalies
3. Verify user permissions for inventory operations
4. Check application logs for detailed error messages
