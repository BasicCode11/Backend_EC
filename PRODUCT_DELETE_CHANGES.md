# Product Delete Behavior Changes

## Summary
Changed product deletion behavior so that variants must be deleted manually before deleting a product, while product images are automatically deleted.

## Changes Made

### 1. Model Changes (`app/models/product_variant.py`)
- Changed `ondelete="CASCADE"` to `ondelete="RESTRICT"` for `product_id` foreign key
- This prevents automatic deletion of variants when product is deleted

### 2. Service Layer (`app/services/product_service.py`)
- Added import: `from app.services.file_service import LogoUpload`
- Added filesystem cleanup for product images before deleting product
- Already had validation checks for:
  - Cannot delete if product has orders
  - Cannot delete if product has variants

### 3. Delete Behavior

**When deleting a product:**

| Related Data | Action | Reason |
|--------------|--------|--------|
| **Product Images** | ✅ AUTO DELETE | Cleaned from filesystem and database |
| **Product Variants** | ❌ MUST DELETE FIRST | User must manually delete variants |
| **Order Items** | ❌ BLOCKED | Cannot delete product with orders |

**Error Messages:**
- `"Cannot delete product with existing orders"` - If product has order history
- `"Cannot Delete Product whit existing variants"` - If product has variants

### 4. Required Database Migration

You need to manually update the foreign key constraint in your database:

```sql
-- MySQL/MariaDB
ALTER TABLE product_variants 
DROP FOREIGN KEY product_variants_ibfk_1;  -- Replace with actual constraint name

ALTER TABLE product_variants
ADD CONSTRAINT product_variants_ibfk_1 
FOREIGN KEY (product_id) 
REFERENCES products(id) 
ON DELETE RESTRICT;
```

**To find your actual constraint name:**
```sql
SHOW CREATE TABLE product_variants;
```

Look for the FOREIGN KEY constraint on `product_id` column.

## Usage Workflow

### To delete a product:

1. **Check for variants:**
   ```
   GET /api/v1/products/{product_id}
   ```

2. **Delete all variants first:**
   ```
   DELETE /api/v1/products/variants/{variant_id}
   ```
   Repeat for each variant.

3. **Then delete the product:**
   ```
   DELETE /api/v1/products/{product_id}
   ```

4. **Product images are automatically deleted** from filesystem

## Benefits

- ✅ Prevents accidental variant deletion
- ✅ Forces explicit cleanup of variants
- ✅ Automatic cleanup of product images
- ✅ Protects order history
- ✅ Clear error messages guide users

## Notes

- Product images are stored in `app/static/images/` and will be deleted from filesystem
- Variant images (if any) are not deleted from filesystem automatically
- Database CASCADE is set for `product_images` table (no changes needed)
