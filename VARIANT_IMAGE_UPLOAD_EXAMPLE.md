# Variant Image Upload Guide

## Overview
The product creation endpoint now supports uploading variant-specific images as files alongside the variant data.

## How It Works

### Request Format
- **Content-Type**: `multipart/form-data`
- **Variant Images Field**: `variant_images` (accepts multiple files)
- **Matching**: Variant images are matched to variants by index order

### Example Request

#### Using cURL:
```bash
curl -X POST "http://localhost:8000/api/v1/products" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "name=T-Shirt" \
  -F "price=29.99" \
  -F "category_id=1" \
  -F "description=Cotton T-Shirt" \
  -F "variants=[{\"sku\":\"TSHIRT-RED-M\",\"variant_name\":\"Red Medium\",\"attributes\":{\"color\":\"Red\",\"size\":\"M\"},\"price\":29.99,\"stock_quantity\":50,\"sort_order\":0},{\"sku\":\"TSHIRT-BLUE-L\",\"variant_name\":\"Blue Large\",\"attributes\":{\"color\":\"Blue\",\"size\":\"L\"},\"price\":32.99,\"stock_quantity\":30,\"sort_order\":1}]" \
  -F "images=@product_main.jpg" \
  -F "variant_images=@red_tshirt.jpg" \
  -F "variant_images=@blue_tshirt.jpg"
```

#### Using Python requests:
```python
import requests

url = "http://localhost:8000/api/v1/products"
headers = {"Authorization": "Bearer YOUR_TOKEN"}

# Prepare form data
data = {
    "name": "T-Shirt",
    "price": 29.99,
    "category_id": 1,
    "description": "Cotton T-Shirt",
    "variants": '[{"sku":"TSHIRT-RED-M","variant_name":"Red Medium","attributes":{"color":"Red","size":"M"},"price":29.99,"stock_quantity":50,"sort_order":0},{"sku":"TSHIRT-BLUE-L","variant_name":"Blue Large","attributes":{"color":"Blue","size":"L"},"price":32.99,"stock_quantity":30,"sort_order":1}]'
}

# Prepare files
files = [
    ("images", ("main.jpg", open("product_main.jpg", "rb"), "image/jpeg")),
    ("variant_images", ("red.jpg", open("red_tshirt.jpg", "rb"), "image/jpeg")),
    ("variant_images", ("blue.jpg", open("blue_tshirt.jpg", "rb"), "image/jpeg"))
]

response = requests.post(url, headers=headers, data=data, files=files)
print(response.json())
```

#### Using JavaScript/FormData:
```javascript
const formData = new FormData();

// Basic fields
formData.append('name', 'T-Shirt');
formData.append('price', 29.99);
formData.append('category_id', 1);
formData.append('description', 'Cotton T-Shirt');

// Variants JSON
const variants = [
  {
    sku: "TSHIRT-RED-M",
    variant_name: "Red Medium",
    attributes: {color: "Red", size: "M"},
    price: 29.99,
    stock_quantity: 50,
    sort_order: 0
  },
  {
    sku: "TSHIRT-BLUE-L",
    variant_name: "Blue Large",
    attributes: {color: "Blue", size: "L"},
    price: 32.99,
    stock_quantity: 30,
    sort_order: 1
  }
];
formData.append('variants', JSON.stringify(variants));

// Main product image
formData.append('images', mainImageFile);

// Variant images (order matters!)
formData.append('variant_images', redTshirtImageFile);  // Goes to first variant
formData.append('variant_images', blueTshirtImageFile); // Goes to second variant

const response = await fetch('http://localhost:8000/api/v1/products', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`
  },
  body: formData
});
```

## Important Notes

1. **Index Matching**: The first `variant_images` file is assigned to the first variant in the JSON array, the second file to the second variant, and so on.

2. **Optional**: Variant images are completely optional. You can:
   - Upload images for all variants
   - Upload images for some variants (first N variants will get images)
   - Upload no variant images (variants will have no image_url)

3. **Fallback**: If a variant has `image_url` in the JSON AND you upload a file, the uploaded file takes precedence.

4. **File Types**: Only PNG, JPG, and JPEG are supported.

5. **Storage**: Images are stored in `app/static/images/` with unique UUIDs.

6. **Response**: The API returns the full product with variants, where each variant's `image_url` field contains the path to the uploaded image.

## Example Response

```json
{
  "id": 1,
  "name": "T-Shirt",
  "price": 29.99,
  "variants": [
    {
      "id": 1,
      "variant_name": "Red Medium",
      "sku": "TSHIRT-RED-M",
      "image_url": "/static/images/a1b2c3d4-e5f6-7890-abcd-ef1234567890.jpg",
      "price": 29.99,
      "stock_quantity": 50
    },
    {
      "id": 2,
      "variant_name": "Blue Large",
      "sku": "TSHIRT-BLUE-L",
      "image_url": "/static/images/f1e2d3c4-b5a6-7890-1234-567890abcdef.jpg",
      "price": 32.99,
      "stock_quantity": 30
    }
  ]
}
```
