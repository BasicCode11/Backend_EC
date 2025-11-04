# Quick Start Guide - E-Commerce Platform

## 🚀 **Start in 3 Steps**

### 1. Run Migrations
```bash
cd "E:\Developer\Back-END\Fastapi\E-commerce"
.venv\Scripts\python.exe -m alembic upgrade head
```

### 2. Start Server
```bash
.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

### 3. Open API Docs
```
http://localhost:8000/docs
```

---

## 📋 **Quick Test Sequence**

### Test Complete Flow (Copy-Paste Ready)

```bash
# 1. Browse Products
curl http://localhost:8000/api/products

# 2. Add to Cart
curl -X POST http://localhost:8000/api/cart/items \
  -H "Content-Type: application/json" \
  -d '{"product_id": 1, "quantity": 2}'

# 3. View Cart
curl http://localhost:8000/api/cart

# 4. Register
curl -X POST http://localhost:8000/api/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@gmail.com",
    "password": "Test123!",
    "first_name": "Test",
    "last_name": "User",
    "phone": "+1234567890"
  }'

# 5. Login
curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@gmail.com", "password": "Test123!"}'

# Save the token from response

# 6. Checkout
curl -X POST http://localhost:8000/api/checkout \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"shipping_address_id": 1}'

# 7. View Orders
curl http://localhost:8000/api/orders/me \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🎯 **Core Endpoints**

### Customer
```
GET  /api/products          - Browse
POST /api/cart/items        - Add to cart
POST /api/checkout          - Place order
GET  /api/orders/me         - My orders
```

### Admin
```
POST /api/products          - Create product
POST /api/inventory         - Manage stock
GET  /api/orders            - All orders
GET  /api/audit-logs        - View logs
```

---

## ✅ **What's Working**

- ✅ Product browsing
- ✅ Shopping cart (guest + user)
- ✅ Order placement
- ✅ **Stock automatically reduces**
- ✅ Order tracking
- ✅ Stock restoration on cancel
- ✅ Inventory management
- ✅ User authentication
- ✅ Permission system
- ✅ Audit logging

---

## 📊 **Key Features**

1. **Stock Management**
   - Automatic reduction on order
   - Automatic restoration on cancel
   - Low stock alerts
   - Telegram notifications

2. **Cart System**
   - Guest carts (session-based)
   - User carts (persistent)
   - Cart merging after login
   - Stock validation

3. **Order System**
   - Complete order lifecycle
   - Status tracking
   - Payment tracking
   - Cancellation support

---

## 🔧 **Configuration**

Edit `.env` file:
```env
SECRET_KEY="your-secret-key"
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_NAME=cms_db
DB_PASSWORD=your_password
```

---

## 📖 **Documentation**

- `FINAL_IMPLEMENTATION_GUIDE.md` - Complete guide
- `STOCK_MANAGEMENT_STRATEGY.md` - Stock system
- `ORDER_FLOW_AND_STOCK_REDUCTION.md` - Order flow
- API Docs: http://localhost:8000/docs

---

## 🎉 **You're Ready!**

Your complete e-commerce platform is running and ready to use!

**Total Routes:** 89+
**Status:** Production Ready ✅
