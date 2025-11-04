# Payment Integration Troubleshooting Guide

## ❌ **Error: "Failed to fetch"**

This error means the frontend cannot connect to your backend API.

---

## 🔍 **Common Causes & Solutions**

### **1. Backend Server Not Running**

**Check if server is running:**

```bash
# Windows
netstat -ano | findstr :8000

# If empty, server is not running!
```

**Solution - Start the server:**

```bash
cd "E:\Developer\Back-END\Fastapi\E-commerce"
.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

**You should see:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

---

### **2. Wrong API URL**

**Check your API URL in the HTML file:**

```javascript
// Should be:
const apiUrl = 'http://localhost:8000';

// NOT:
const apiUrl = 'http://127.0.0.1:8000'; // Might cause CORS issues
const apiUrl = 'https://localhost:8000'; // Wrong protocol
const apiUrl = 'http://localhost:8080'; // Wrong port
```

---

### **3. CORS Policy Error**

**Error in browser console:**
```
Access to fetch at 'http://localhost:8000' from origin 'null' 
has been blocked by CORS policy
```

**Check your `.env` file:**
```env
# Make sure this includes file:// origin for local HTML files
ALLOWED_ORIGINS=["http://localhost:8000","http://localhost:3000","http://127.0.0.1:8000","null"]
```

**Or update main.py temporarily:**
```python
# In app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

### **4. Authentication Required**

If your endpoint requires authentication, you need a valid token.

**Get a token first:**

```bash
# Login to get token
curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "your_password"}'

# Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Use the token in the HTML file:**
```html
<input type="text" id="authToken" value="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...">
```

---

### **5. Order Doesn't Exist**

**Check if order exists:**

```bash
# Check existing orders
curl http://localhost:8000/api/orders \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Create an order first if needed:**

```bash
# 1. Add items to cart
POST http://localhost:8000/api/cart/items
{
  "product_id": 1,
  "quantity": 2
}

# 2. Checkout (creates order)
POST http://localhost:8000/api/checkout
{
  "shipping_address_id": 1
}
```

---

## ✅ **Complete Testing Checklist**

### **Step 1: Verify Backend is Running**

```bash
# Start server
cd "E:\Developer\Back-END\Fastapi\E-commerce"
.venv\Scripts\python.exe -m uvicorn app.main:app --reload

# Test health check
curl http://localhost:8000/
# Should return: {"message": "Welcome to..."}
```

### **Step 2: Test Payment Endpoint Directly**

```bash
# Test without auth (if public)
curl -X POST http://localhost:8000/api/payments/aba-payway/checkout \
  -H "Content-Type: application/json" \
  -d '{"order_id": 1}'

# Or with auth
curl -X POST http://localhost:8000/api/payments/aba-payway/checkout \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"order_id": 1}'
```

**Expected response:**
```json
{
  "transaction_id": "ORD1_...",
  "checkout_url": "https://checkout-sandbox.payway.com.kh/...",
  "payment_data": { ... }
}
```

### **Step 3: Check Browser Console**

Open browser Developer Tools (F12) and check Console tab for errors.

**Common errors:**

1. **Network Error:**
   ```
   Failed to fetch
   ```
   → Server not running

2. **CORS Error:**
   ```
   CORS policy blocked
   ```
   → Update CORS settings

3. **401 Unauthorized:**
   ```
   {"detail": "Not authenticated"}
   ```
   → Need valid token

4. **404 Not Found:**
   ```
   {"detail": "Order not found"}
   ```
   → Order doesn't exist

---

## 🚀 **Alternative: Skip Frontend, Use Direct Form**

If you're having trouble with the API call, use the direct form method:

### **Method 1: Use Static HTML (No API Call)**

I already created this for you: **`test_aba_payment.html`**

This file has your payment data hardcoded - no API call needed!

```bash
# Just open this file:
test_aba_payment.html

# Click the button
# ✅ Works without backend!
```

---

### **Method 2: Create Simple Form**

```html
<!DOCTYPE html>
<html>
<head>
    <title>Pay Now</title>
</head>
<body>
    <h1>Pay $400.00</h1>
    
    <form method="POST" action="https://checkout-sandbox.payway.com.kh/api/payment-gateway/v1/payments/purchase">
        <!-- Paste your payment data here -->
        <input type="hidden" name="req_time" value="20251102154955">
        <input type="hidden" name="merchant_id" value="ec462423">
        <input type="hidden" name="tran_id" value="ORD4_20251102154955">
        <input type="hidden" name="amount" value="400.00">
        <input type="hidden" name="hash" value="87ea0f056299862056430c6cef95b2047967b89670f6de14670accb83b488d46">
        <input type="hidden" name="return_url" value="http://localhost:8000/payment/callback">
        <input type="hidden" name="continue_url" value="http://localhost:8000/order-success">
        <input type="hidden" name="cancel_url" value="http://localhost:8000/cart">
        <input type="hidden" name="payment_option" value="abapay">
        <input type="hidden" name="currency" value="USD">
        <input type="hidden" name="items" value='[{"name": "Order #ORD-20251102-38ADD3C0", "quantity": "20", "price": "400.00"}]'>
        <input type="hidden" name="shipping" value="0.00">
        <input type="hidden" name="firstname" value="Admin">
        <input type="hidden" name="lastname" value="User">
        <input type="hidden" name="email" value="admin@example.com">
        <input type="hidden" name="phone" value="+1234567890">
        
        <button type="submit" style="padding: 15px 30px; font-size: 16px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;">
            💳 Proceed to Payment
        </button>
    </form>
</body>
</html>
```

Save as `simple_payment.html` and open in browser. **No backend needed!**

---

## 📊 **Debugging Flow Chart**

```
Is backend server running?
    ├─ NO → Start server: uvicorn app.main:app --reload
    └─ YES
        ↓
Can you access http://localhost:8000/?
    ├─ NO → Check firewall, port conflicts
    └─ YES
        ↓
Can you call API with curl?
    ├─ NO → Check authentication, order exists
    └─ YES
        ↓
Does browser console show CORS error?
    ├─ YES → Update CORS settings in .env
    └─ NO
        ↓
✅ Should work! Try again.

If still fails → Use test_aba_payment.html (no API needed)
```

---

## ✅ **Quick Solutions**

### **Solution 1: Test Without API Call**

```bash
# Just open this file:
test_aba_payment.html

# Click button → Payment page loads ✅
# No backend needed for this test!
```

### **Solution 2: Test Backend First**

```bash
# 1. Start backend
.venv\Scripts\python.exe -m uvicorn app.main:app --reload

# 2. Test in browser
http://localhost:8000/docs

# 3. Try payment endpoint in Swagger UI
```

### **Solution 3: Use curl**

```bash
# Get payment data via curl
curl -X POST http://localhost:8000/api/payments/aba-payway/checkout \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"order_id": 4}'

# Copy response and use in HTML form
```

---

## 🎯 **Recommended Quick Test**

### **Option A: No Backend Needed**

```
1. Open: test_aba_payment.html
2. Click button
3. ✅ Should work!
```

### **Option B: With Backend**

```bash
# Terminal 1: Start backend
.venv\Scripts\python.exe -m uvicorn app.main:app --reload

# Browser: Open
http://localhost:8000/docs

# Swagger UI: Try
POST /api/payments/aba-payway/checkout
{
  "order_id": 4
}

# Copy payment_data from response
# Paste into HTML form
```

---

## 📝 **Summary**

| Error | Cause | Solution |
|-------|-------|----------|
| Failed to fetch | Server not running | Start uvicorn |
| CORS error | Origin not allowed | Update CORS settings |
| 401 Unauthorized | No/invalid token | Get token via /api/login |
| 404 Not Found | Order doesn't exist | Create order first |
| Connection refused | Wrong port/URL | Check URL is localhost:8000 |

---

## 🚀 **Easiest Solution Right Now**

**Just use the file I created:**

```
test_aba_payment.html
```

**This file:**
- ✅ Has your payment data already
- ✅ Doesn't need backend API
- ✅ Doesn't need authentication
- ✅ Just click and it works!

**Open it now!** 🎯
