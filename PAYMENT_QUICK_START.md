# ABA PayWay Payment - Quick Start

## 🚀 **3-Step Setup**

### 1. Install Dependency
```bash
.venv\Scripts\python.exe -m pip install pycryptodome
```

### 2. Update .env
```env
ABA_PAYWAY_MERCHANT_ID=ec462423
ABA_PAYWAY_PUBLIC_KEY=1fd5c1490c05370dd74af1e22a4d4ef9dab6086a
# (Other keys already in .env.example)
```

### 3. Start Server
```bash
.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

---

## 💳 **Test Payment Flow**

### Customer Journey:

```javascript
// 1. Place Order
POST /api/checkout
{
  "shipping_address_id": 1
}
// Returns: order with order_id

// 2. Initiate Payment
POST /api/payments/aba-payway/checkout
{
  "order_id": 123
}
// Returns: checkout_url

// 3. Redirect User
window.location.href = checkout_url;
// User pays on ABA PayWay

// 4. Handle Return
// ABA redirects to: /api/payments/aba-payway/return?status=0&tran_id=...
if (status === '0') {
  // Payment successful!
}
```

---

## 📝 **Complete Example**

```javascript
async function completeCheckout() {
  // 1. Place order
  const orderResponse = await fetch('/api/checkout', {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer ' + token,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      shipping_address_id: 1
    })
  });
  const order = await orderResponse.json();
  
  // 2. Initiate payment
  const paymentResponse = await fetch('/api/payments/aba-payway/checkout', {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer ' + token,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      order_id: order.id,
      return_url: window.location.origin + '/payment/callback'
    })
  });
  const payment = await paymentResponse.json();
  
  // 3. Redirect to ABA PayWay
  window.location.href = payment.checkout_url;
}

// On callback page
function handleCallback() {
  const params = new URLSearchParams(window.location.search);
  const status = params.get('status');
  
  if (status === '0') {
    showSuccess('Payment completed!');
  } else {
    showError('Payment failed!');
  }
}
```

---

## ✅ **What Works**

- ✅ Payment initiation
- ✅ ABA PayWay redirect
- ✅ Payment processing
- ✅ Callback handling
- ✅ Order status update
- ✅ Audit logging

---

## 📖 **Full Documentation**

See: `ABA_PAYWAY_INTEGRATION_GUIDE.md`

---

**Status:** ✅ Ready to Use
**Environment:** Sandbox (Testing)
