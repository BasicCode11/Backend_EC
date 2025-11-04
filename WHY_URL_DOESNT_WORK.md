# Why You Can't Paste ABA PayWay URL in Browser

## 🚫 **The Problem**

When you paste the ABA PayWay URL in browser:
```
https://checkout-sandbox.payway.com.kh/api/payment-gateway/v1/payments/purchase
```

**You get:**
```
405 Method Not Allowed
```

---

## ❓ **Why This Happens**

### **Browser Behavior:**

```
When you paste URL in browser:
└─> Browser sends GET request
    └─> ABA PayWay API expects POST
        └─> 405 Method Not Allowed ❌
```

### **What ABA PayWay Expects:**

```
POST request with form data:
├─> req_time
├─> merchant_id
├─> tran_id
├─> amount
├─> hash
├─> return_url
├─> continue_url
├─> cancel_url
├─> payment_option
├─> currency
├─> items
├─> shipping
├─> firstname
├─> lastname
├─> email
└─> phone
```

---

## ✅ **How to Fix**

### **Option 1: Use Test HTML File (Easiest)**

I created `test_aba_payment.html` for you with your exact payment data.

**Steps:**
1. Open `test_aba_payment.html` in browser
2. Click "Proceed to Payment" button
3. Form automatically POSTs to ABA PayWay
4. ✅ Payment page loads!

---

### **Option 2: Create Dynamic Form (Your App)**

```javascript
// When customer clicks "Pay Now"
async function initiatePayment(orderId) {
    // 1. Get payment data from your backend
    const response = await fetch('/api/payments/aba-payway/checkout', {
        method: 'POST',
        headers: {
            'Authorization': 'Bearer ' + token,
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
    
    // 2. Create and submit form
    createAndSubmitForm(data);
}

function createAndSubmitForm(paymentData) {
    // Create form element
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = paymentData.checkout_url;
    
    // Add all payment fields as hidden inputs
    for (const [key, value] of Object.entries(paymentData.payment_data)) {
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = key;
        input.value = value;
        form.appendChild(input);
    }
    
    // Add form to page (hidden) and submit
    document.body.appendChild(form);
    form.submit(); // This redirects to ABA PayWay
}
```

---

### **Option 3: Auto-Submit Form Page**

```html
<!DOCTYPE html>
<html>
<head>
    <title>Redirecting to Payment...</title>
</head>
<body>
    <h2>Please wait...</h2>
    <p>Redirecting to ABA PayWay</p>
    
    <form id="paymentForm" method="POST" action="{{checkout_url}}">
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
        <input type="hidden" name="items" value="{{items}}">
        <input type="hidden" name="shipping" value="0.00">
        <input type="hidden" name="firstname" value="{{firstname}}">
        <input type="hidden" name="lastname" value="{{lastname}}">
        <input type="hidden" name="email" value="{{email}}">
        <input type="hidden" name="phone" value="{{phone}}">
    </form>
    
    <script>
        // Auto-submit on page load
        document.getElementById('paymentForm').submit();
    </script>
</body>
</html>
```

---

## 📊 **Comparison**

| Method | Result |
|--------|--------|
| Paste URL in browser | ❌ 405 Error |
| GET request | ❌ 405 Error |
| POST with form data | ✅ Works! |
| JavaScript form.submit() | ✅ Works! |
| HTML auto-submit form | ✅ Works! |

---

## 🧪 **Test Now**

### **Quick Test:**

1. **Open the file I created:**
   ```
   test_aba_payment.html
   ```

2. **Click the button**
   - Don't paste URL
   - Don't type in browser
   - Just click the button!

3. **You'll see ABA PayWay page** ✅

---

## 💡 **Understanding HTTP Methods**

### **GET vs POST:**

```
GET (Browser URL paste):
- No request body
- Data in URL only
- Used for viewing pages
❌ ABA PayWay doesn't accept this

POST (Form submit):
- Has request body
- Data sent securely
- Used for submitting forms
✅ ABA PayWay requires this
```

### **Your Payment Data:**

```json
{
  "req_time": "20251102154955",
  "merchant_id": "ec462423",
  "tran_id": "ORD4_20251102154955",
  "amount": "400.00",
  "hash": "87ea0...",
  ...
}
```

**This MUST be sent as POST form data, not in URL!**

---

## ✅ **Correct Flow**

```
Step 1: Backend API Call
POST /api/payments/aba-payway/checkout
→ Returns payment_data

Step 2: Create Form (Frontend)
<form method="POST" action="{{checkout_url}}">
  <input name="req_time" value="...">
  <input name="merchant_id" value="...">
  ...
</form>

Step 3: Submit Form
form.submit()
→ Browser POSTs to ABA PayWay

Step 4: Payment Page Loads
✅ Customer sees ABA PayWay payment options

Step 5: Customer Pays
→ ABA processes payment

Step 6: Redirect Back
→ Customer returns to your site
```

---

## 🚀 **Quick Solution**

**Use the HTML file I created:**

```bash
# Open this file in your browser:
test_aba_payment.html

# Click "Proceed to Payment"
# ✅ It will work!
```

**The file has your exact payment data already filled in!**

---

## 📝 **Summary**

### **Why URL doesn't work:**
- ❌ Browser sends GET request
- ❌ ABA PayWay needs POST request
- ❌ Payment data must be in form body

### **What works:**
- ✅ HTML form with method="POST"
- ✅ JavaScript form.submit()
- ✅ Button that submits form

### **What you need to do:**
1. ✅ Open `test_aba_payment.html`
2. ✅ Click the button
3. ✅ Complete payment
4. ✅ Done!

---

**Don't paste URL! Use the HTML file!** 🎯
