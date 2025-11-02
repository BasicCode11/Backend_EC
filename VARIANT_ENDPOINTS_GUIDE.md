# Product Variant Endpoints Guide

## Available Endpoints

### 1. POST `/products/{product_id}/variants` - Add Variant
Create a new variant for a product.

**Authentication:** Required (products:update permission)

**Request:**
- Content-Type: `multipart/form-data`
- Path: `product_id` (integer)
- Body:
  - `variant_name` (string, required) - Name of the variant
  - `sku` (string, optional) - SKU code
  - `attributes` (JSON string, optional) - Variant attributes like `{"color": "Red", "size": "M"}`
  - `price` (decimal, optional) - Variant-specific price (uses product price if not set)
  - `stock_quantity` (integer, default: 0) - Stock quantity
  - `sort_order` (integer, default: 0) - Display order
  - `variant_image` (file, optional) - Image file for this variant

**Example using cURL:**
```bash
curl -X POST "http://localhost:8000/api/v1/products/1/variants" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "variant_name=Red Medium" \
  -F "sku=PROD-RED-M" \
  -F "attributes={\"color\":\"Red\",\"size\":\"M\"}" \
  -F "price=29.99" \
  -F "stock_quantity=50" \
  -F "sort_order=0" \
  -F "variant_image=@red_shirt.jpg"
```

**Example using JavaScript:**
```javascript
const formData = new FormData();
formData.append('variant_name', 'Red Medium');
formData.append('sku', 'PROD-RED-M');
formData.append('attributes', JSON.stringify({color: 'Red', size: 'M'}));
formData.append('price', 29.99);
formData.append('stock_quantity', 50);
formData.append('sort_order', 0);
formData.append('variant_image', imageFile); // File object

const response = await fetch('http://localhost:8000/api/v1/products/1/variants', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`
  },
  body: formData
});
```

**Response (201 Created):**
```json
{
  "id": 1,
  "product_id": 1,
  "variant_name": "Red Medium",
  "sku": "PROD-RED-M",
  "attributes": {"color": "Red", "size": "M"},
  "price": 29.99,
  "stock_quantity": 50,
  "image_url": "/static/images/a1b2c3d4-e5f6-7890-abcd-ef1234567890.jpg",
  "sort_order": 0,
  "created_at": "2025-11-01T10:00:00Z",
  "updated_at": "2025-11-01T10:00:00Z"
}
```

---

### 2. PUT `/products/variants/{variant_id}` - Update Variant
Update an existing variant.

**Authentication:** Required (products:update permission)

**Request:**
- Content-Type: `multipart/form-data`
- Path: `variant_id` (integer)
- Body: Form data with fields to update (all optional)
  - `variant_name` (string)
  - `sku` (string)
  - `attributes` (JSON string)
  - `price` (decimal)
  - `stock_quantity` (integer)
  - `sort_order` (integer)
  - `variant_image` (file) - replaces existing image

**Example using cURL:**
```bash
curl -X PUT "http://localhost:8000/api/v1/products/variants/1" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "variant_name=Red Large" \
  -F "price=32.99" \
  -F "stock_quantity=75" \
  -F "variant_image=@new_red_large.jpg"
```

**JavaScript (with file upload):**
```javascript
const formData = new FormData();
formData.append('variant_name', 'Red Large');
formData.append('price', 32.99);
formData.append('stock_quantity', 75);
formData.append('variant_image', newImageFile); // Optional

const response = await fetch('http://localhost:8000/api/v1/products/variants/1', {
  method: 'PUT',
  headers: {
    'Authorization': `Bearer ${token}`
  },
  body: formData
});
```

**JavaScript (update without image):**
```javascript
const formData = new FormData();
formData.append('stock_quantity', 75);

const response = await fetch('http://localhost:8000/api/v1/products/variants/1', {
  method: 'PUT',
  headers: {
    'Authorization': `Bearer ${token}`
  },
  body: formData
});
```

**Response (200 OK):**
```json
{
  "id": 1,
  "product_id": 1,
  "variant_name": "Red Large",
  "sku": "PROD-RED-M",
  "attributes": {"color": "Red", "size": "M"},
  "price": 32.99,
  "stock_quantity": 75,
  "image_url": "/static/images/a1b2c3d4-e5f6-7890-abcd-ef1234567890.jpg",
  "sort_order": 0,
  "created_at": "2025-11-01T10:00:00Z",
  "updated_at": "2025-11-01T10:15:00Z"
}
```

---

### 3. DELETE `/products/variants/{variant_id}` - Delete Variant
Delete a variant and its image from filesystem.

**Authentication:** Required (products:update permission)

**Request:**
- Path: `variant_id` (integer)

**Note:** This will also delete the variant image from the filesystem if it exists.

**Example:**
```bash
curl -X DELETE "http://localhost:8000/api/v1/products/variants/1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**JavaScript:**
```javascript
const response = await fetch('http://localhost:8000/api/v1/products/variants/1', {
  method: 'DELETE',
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
```

**Response (200 OK):**
```json
{
  "message": "Variant deleted successfully"
}
```

---

## Common Use Cases

### Add Multiple Variants to a Product

```javascript
const variants = [
  { name: 'Red Small', attributes: {color: 'Red', size: 'S'}, price: 29.99, stock: 50 },
  { name: 'Red Medium', attributes: {color: 'Red', size: 'M'}, price: 29.99, stock: 75 },
  { name: 'Blue Small', attributes: {color: 'Blue', size: 'S'}, price: 32.99, stock: 40 }
];

for (const variant of variants) {
  const formData = new FormData();
  formData.append('variant_name', variant.name);
  formData.append('attributes', JSON.stringify(variant.attributes));
  formData.append('price', variant.price);
  formData.append('stock_quantity', variant.stock);
  
  await fetch(`http://localhost:8000/api/v1/products/${productId}/variants`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: formData
  });
}
```

### Update Variant Stock

```javascript
await fetch(`http://localhost:8000/api/v1/products/variants/${variantId}`, {
  method: 'PUT',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ stock_quantity: 100 })
});
```

### Delete All Variants Before Deleting Product

```javascript
// 1. Get product with variants
const product = await fetch(`http://localhost:8000/api/v1/products/${productId}`)
  .then(r => r.json());

// 2. Delete all variants
for (const variant of product.variants) {
  await fetch(`http://localhost:8000/api/v1/products/variants/${variant.id}`, {
    method: 'DELETE',
    headers: { 'Authorization': `Bearer ${token}` }
  });
}

// 3. Now delete the product
await fetch(`http://localhost:8000/api/v1/products/${productId}`, {
  method: 'DELETE',
  headers: { 'Authorization': `Bearer ${token}` }
});
```

---

## Notes

1. **Variant images** are uploaded as files and stored in `app/static/images/`
2. **Attributes** must be valid JSON when sent as string
3. **Price** is optional - if not set, uses the product's base price
4. **Stock quantity** defaults to 0 if not provided
5. **Variants must be deleted** before deleting the parent product
6. All endpoints require **authentication** and appropriate permissions
7. **UPDATE endpoint** replaces the old variant image when uploading a new one (old image is deleted from filesystem)
8. **DELETE endpoint** automatically removes the variant image from filesystem
