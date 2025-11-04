# ABA PayWay Integration Fix - Form POST Method

## 🐛 **Problem**

**Error:**
```
422: Payment gateway error: Redirect response '302 Found'
Redirect location: 'https://checkout-sandbox.payway.com.kh/checkout/...'
Message: "Invalid Transaction ID."
```

**Root Cause:**
ABA PayWay **doesn't accept** direct JSON POST requests from backend. It requires an HTML **form POST** from the **frontend** (browser).

---

## ✅ **Solution**

### **How ABA PayWay Actually Works:**

```
❌ WRONG (What we were doing):
Backend → POST JSON → ABA PayWay API
                ↓
              302 Redirect (Error!)

✅ CORRECT (What we should do):
Backend → Generate payment data
    ↓
Frontend receives data
    ↓
Frontend → POST HTML Form → ABA PayWay
    ↓
ABA PayWay shows payment page
```

### **Why Form POST is Required:**

ABA PayWay needs the request to come from a **browser** so they can:
1. Set cookies for session tracking
2. Redirect user through payment pages
3. Return user to your site after payment

---

## 🔧 **Fixed Implementation**

### **Backend (API) Changes:**

**Before (Broken):**
```python
# Tried to POST JSON directly
response = httpx.post(
    settings.ABA_PAYWAY_API_URL,
    json=payload,  # ❌ ABA doesn't accept this
    timeout=30.0
)
# Result: 302 redirect error
```

**After (Fixed):**
```python
# Just prepare the data for frontend
payment.gateway_response["checkout_payload"] = payload
checkout_url = settings.ABA_PAYWAY_API_URL

return ABAPayWayCheckoutResponse(
    transaction_id=transaction_id,
    checkout_url=checkout_url,
    payment_data=payload,  # ✅ Frontend will POST this
    expires_at=None
)
```

### **Frontend Implementation:**

**Method 1: Auto-Submit Form (Recommended)**

```html
<!DOCTYPE html>
<html>
<body>
    <h2>Redirecting to Payment Gateway...</h2>
    <p>Please wait while we redirect you to ABA PayWay</p>
    
    <form id="abaPaymentForm" method="POST" action="{{checkout_url}}">
        <input type="hidden" name="req_time" value="{{req_time}}">
        <input type="hidden" name="merchant_id" value="{{merchant_id}}">
        <input type="hidden" name="tran_id" value="{{tran_id}}">
        <input type="hidden" name="amount" value="{{amount}}">
        <input type="hidden" name="hash" value="{{hash}}">
        <input type="hidden" name="return_url" value="{{return_url}}">
        <input type="hidden" name="continue_url" value="{{continue_url}}">
        <input type="hidden" name="cancel_url" value="{{cancel_url}}">
        <input type="hidden" name="payment_option" value="abapay">
        <input type="hidden" name="currency" value="USD">
        <input type="hidden" name="firstname" value="{{firstname}}">
        <input type="hidden" name="lastname" value="{{lastname}}">
        <input type="hidden" name="email" value="{{email}}">
        <input type="hidden" name="phone" value="{{phone}}">
        <input type="hidden" name="items" value="{{items}}">
        <input type="hidden" name="shipping" value="0.00">
    </form>
    
    <script>
        // Auto-submit form on page load
        document.getElementById('abaPaymentForm').submit();
    </script>
</body>
</html>
```

**Method 2: JavaScript POST**

```javascript
async function initiatePayment(orderId) {
    // 1. Get payment data from backend
    const response = await fetch('/api/payments/aba-payway/checkout', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            order_id: orderId,
            return_url: window.location.origin + '/payment/callback',
            continue_url: window.location.origin + '/order-success',
            cancel_url: window.location.origin + '/cart'
        })
    });
    
    const data = await response.json();
    
    // 2. Create hidden form
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = data.checkout_url;
    
    // 3. Add all payment data as hidden inputs
    for (const [key, value] of Object.entries(data.payment_data)) {
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = key;
        input.value = value;
        form.appendChild(input);
    }
    
    // 4. Add form to page and submit
    document.body.appendChild(form);
    form.submit();
}
```

**Method 3: React/Vue Component**

```javascript
// React Example
import React, { useEffect, useRef } from 'react';

function ABAPaymentRedirect({ paymentData }) {
    const formRef = useRef(null);
    
    useEffect(() => {
        // Auto-submit when component mounts
        if (formRef.current) {
            formRef.current.submit();
        }
    }, []);
    
    return (
        <div className="payment-redirect">
            <h2>Redirecting to Payment...</h2>
            <p>Please wait...</p>
            
            <form 
                ref={formRef}
                method="POST" 
                action={paymentData.checkout_url}
            >
                {Object.entries(paymentData.payment_data).map(([key, value]) => (
                    <input 
                        key={key}
                        type="hidden" 
                        name={key} 
                        value={value} 
                    />
                ))}
            </form>
        </div>
    );
}

// Usage:
function CheckoutPage() {
    const [paymentData, setPaymentData] = useState(null);
    
    const handlePayment = async (orderId) => {
        const response = await fetch('/api/payments/aba-payway/checkout', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ order_id: orderId })
        });
        
        const data = await response.json();
        setPaymentData(data);
    };
    
    if (paymentData) {
        return <ABAPaymentRedirect paymentData={paymentData} />;
    }
    
    return (
        <button onClick={() => handlePayment(123)}>
            Proceed to Payment
        </button>
    );
}
```

---

## 📊 **Complete Payment Flow**

### **Step-by-Step:**

```
1. Customer Clicks "Pay Now"
   └─> Frontend: fetch('/api/payments/aba-payway/checkout')

2. Backend Prepares Payment Data
   └─> Creates payment record
   └─> Generates transaction ID
   └─> Creates hash
   └─> Returns: {
         transaction_id: "ORD123_...",
         checkout_url: "https://checkout-sandbox.payway.com.kh/...",
         payment_data: { req_time, merchant_id, tran_id, amount, hash, ... }
       }

3. Frontend Receives Data
   └─> Creates HTML form
   └─> Populates hidden fields with payment_data
   └─> Auto-submits form

4. Browser POSTs Form to ABA PayWay
   └─> ABA PayWay receives request
   └─> Validates hash
   └─> Shows payment page to customer

5. Customer Completes Payment
   └─> Enters PIN / scans QR code
   └─> Confirms payment

6. ABA PayWay Sends Callback
   └─> POST to your return_url with status
   └─> Your backend verifies hash
   └─> Updates payment status

7. Customer Redirected Back
   └─> To continue_url (success) or cancel_url
   └─> Shows order confirmation
```

---

## 🧪 **Testing**

### **Backend API Test:**

```bash
POST /api/payments/aba-payway/checkout
Authorization: Bearer {token}
Content-Type: application/json

{
  "order_id": 123
}

# Response: ✅ Success
{
  "transaction_id": "ORD123_20251102154530",
  "checkout_url": "https://checkout-sandbox.payway.com.kh/api/payment-gateway/v1/payments/purchase",
  "payment_data": {
    "req_time": "20251102154530",
    "merchant_id": "ec462423",
    "tran_id": "ORD123_20251102154530",
    "amount": "150.00",
    "hash": "abc123...",
    "return_url": "http://localhost:8000/payment/callback",
    "continue_url": "http://localhost:8000/order-success",
    "cancel_url": "http://localhost:8000/cart",
    "payment_option": "abapay",
    "currency": "USD",
    ...
  }
}
```

### **Frontend Test:**

```html
<!-- Save this as test_payment.html -->
<!DOCTYPE html>
<html>
<head>
    <title>Test ABA Payment</title>
</head>
<body>
    <h1>Test ABA PayWay Integration</h1>
    <button onclick="testPayment()">Test Payment</button>
    
    <script>
        async function testPayment() {
            // Get payment data
            const response = await fetch('http://localhost:8000/api/payments/aba-payway/checkout', {
                method: 'POST',
                headers: {
                    'Authorization': 'Bearer YOUR_TOKEN',
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    order_id: 123
                })
            });
            
            const data = await response.json();
            console.log('Payment data:', data);
            
            // Create and submit form
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = data.checkout_url;
            
            for (const [key, value] of Object.entries(data.payment_data)) {
                const input = document.createElement('input');
                input.type = 'hidden';
                input.name = key;
                input.value = value;
                form.appendChild(input);
            }
            
            document.body.appendChild(form);
            form.submit();
        }
    </script>
</body>
</html>
```

---

## 📝 **API Response Structure**

### **New Response Format:**

```json
{
  "transaction_id": "ORD123_20251102154530",
  "checkout_url": "https://checkout-sandbox.payway.com.kh/api/payment-gateway/v1/payments/purchase",
  "payment_data": {
    "req_time": "20251102154530",
    "merchant_id": "ec462423",
    "tran_id": "ORD123_20251102154530",
    "amount": "150.00",
    "hash": "generated_hash_here",
    "return_url": "http://yoursite.com/payment/callback",
    "continue_url": "http://yoursite.com/order-success",
    "cancel_url": "http://yoursite.com/cart",
    "payment_option": "abapay",
    "currency": "USD",
    "items": "[{\"name\":\"Order #ORD-123\",\"quantity\":\"1\",\"price\":\"150.00\"}]",
    "shipping": "0.00",
    "firstname": "John",
    "lastname": "Doe",
    "email": "john@example.com",
    "phone": "+855123456789"
  },
  "expires_at": null
}
```

---

## ✅ **Summary**

### **What Changed:**

| Before | After |
|--------|-------|
| Backend POSTs JSON to ABA | ❌ Doesn't work |
| Backend prepares data | ✅ Works |
| Frontend receives URL only | ❌ Not enough |
| Frontend receives URL + data | ✅ Complete |
| Frontend POSTs form to ABA | ✅ Correct way |

### **Key Points:**

1. ✅ Backend prepares payment data (hash, amount, etc.)
2. ✅ Frontend receives data via API
3. ✅ Frontend creates HTML form
4. ✅ Frontend auto-submits form to ABA PayWay
5. ✅ Browser POSTs to ABA (not backend!)
6. ✅ ABA processes payment
7. ✅ ABA sends callback to backend
8. ✅ ABA redirects customer back to your site

---

## 🚀 **Next Steps**

1. ✅ Backend API is ready (returns payment_data)
2. ⏳ Implement frontend form POST
3. ⏳ Test complete payment flow
4. ⏳ Handle payment callback
5. ⏳ Update order status

---

**Fixed:** 2025-11-02  
**Status:** ✅ Backend Ready, Frontend Implementation Needed  
**Method:** Form POST (not JSON)
