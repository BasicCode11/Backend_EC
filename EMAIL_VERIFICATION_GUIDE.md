# 📧 Email Verification - User Guide

## ✅ Improved User Experience

Your email verification system has been **improved for better usability**!

---

## 🎯 What Changed?

### Before (Confusing):
❌ Register → Can't login until email verified → User confused → Bad experience

### After (User-Friendly):
✅ Register → Login immediately → Friendly reminder to verify email → Good experience

---

## 📝 How It Works Now

### 1️⃣ **User Registration**

**Endpoint:** `POST /api/register`

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "1234567890"
}
```

**Response:**
```json
{
  "message": "Registration successful! You can now login.",
  "user": {
    "id": 10,
    "uuid": "abc-123",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role_id": 4,
    "email_verified": false
  },
  "email_verified": false,
  "next_steps": [
    "Login with your credentials at /api/login",
    "Check your email for verification link",
    "Verify your email to unlock all features"
  ],
  "note": "In development mode, check application logs for the verification link"
}
```

### 2️⃣ **User Can Login Immediately**

**Endpoint:** `POST /api/login`

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response (If Email NOT Verified):**
```json
{
  "access_token": "eyJhbGciOiJ...",
  "token_type": "bearer",
  "refresh_token": null,
  "user": {
    "id": 10,
    "email": "user@example.com",
    "email_verified": false
  },
  "warning": "Please verify your email to unlock all features",
  "action": "Use /api/resend-verification to get a new verification link"
}
```

**Response (If Email IS Verified):**
```json
{
  "access_token": "eyJhbGciOiJ...",
  "token_type": "bearer",
  "refresh_token": null,
  "user": {
    "id": 10,
    "email": "user@example.com",
    "email_verified": true
  }
}
```

### 3️⃣ **Getting Verification Token (Development)**

Since you're in development mode without actual email sending:

**Option A: Check Application Logs**
```
Look for output like:
================================================================================
[EMAIL] To: user@example.com
[EMAIL] Subject: Verify Your Email Address
[EMAIL] Content:
http://localhost:3000/verify-email/abc123xyz...
================================================================================
```

**Option B: Use Dev Endpoint**
```bash
# 1. First resend verification email
POST /api/resend-verification
{
  "email": "user@example.com"
}

# 2. Then get the token
GET /api/dev/get-verification-token/user@example.com

# Response:
{
  "email": "user@example.com",
  "token": "abc123xyz...",
  "verification_link": "http://localhost:8000/api/verify-email/abc123xyz...",
  "expires_at": "2025-10-30T14:30:00Z",
  "is_valid": true
}
```

### 4️⃣ **Verify Email**

**Endpoint:** `GET /api/verify-email/{token}`

```bash
GET /api/verify-email/abc123xyz...
```

**Response:**
```json
{
  "message": "Email verified successfully"
}
```

---

## 🔧 Complete Flow Example

### Scenario: New User Registration and Verification

```bash
# Step 1: Register
curl -X POST http://localhost:8000/api/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@test.com",
    "password": "Test123!",
    "first_name": "New",
    "last_name": "User"
  }'

# Response shows: "You can now login" + email_verified: false

# Step 2: Login immediately (no waiting!)
curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@test.com",
    "password": "Test123!"
  }'

# Response includes warning: "Please verify your email"
# But you get access_token and can use the app!

# Step 3: Get verification token (DEV ONLY)
curl http://localhost:8000/api/dev/get-verification-token/newuser@test.com

# Step 4: Verify email
curl http://localhost:8000/api/verify-email/{token_from_step_3}

# Step 5: Login again - no more warning!
curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@test.com",
    "password": "Test123!"
  }'

# Now response has no warning - fully verified!
```

---

## 🎨 Frontend Integration Tips

### Show Verification Banner

```javascript
// After login, check if email is verified
if (loginResponse.warning) {
  // Show banner at top of page
  showBanner({
    message: loginResponse.warning,
    action: loginResponse.action,
    type: 'info'
  });
}
```

### Example Banner HTML
```html
<div class="verification-banner">
  ⚠️ Please verify your email to unlock all features.
  <button onclick="resendVerification()">Resend Email</button>
</div>
```

---

## 🔐 Security Notes

1. **Users CAN login without verification** - This is intentional for better UX
2. **Some features can be restricted** - Check `user.email_verified` on backend
3. **Tokens expire in 24 hours** - After that, user must request a new one
4. **One-time use** - Each token can only be used once

---

## 🚀 Production Deployment

Before going to production:

### 1. Configure Real Email Service

Update `app/services/email_service.py`:
```python
# Replace the logging with actual email sending
# Options:
# - SMTP (Gmail, Outlook, etc.)
# - SendGrid
# - AWS SES
# - Mailgun
# - Postmark
```

### 2. Remove Dev Endpoint

Delete this from `auth_router.py`:
```python
@router.get("/dev/get-verification-token/{email}")
def get_verification_token_dev(...)
```

### 3. Update Frontend URL

In `.env` file:
```
FRONTEND_URL=https://your-production-domain.com
```

---

## ❓ FAQ

**Q: Why can users login without verifying email?**
A: Better user experience. Users can explore the app immediately, verify email later.

**Q: Should I block unverified users from certain features?**
A: Yes! For example:
- Can't make purchases until verified
- Can't post reviews until verified
- Can't change sensitive settings until verified

**Q: How do I check verification status in my code?**
A: Access `user.email_verified` from the authenticated user object.

**Q: What if user never verifies email?**
A: They can still use basic features. Send reminder emails periodically.

---

## 🎯 Summary

✅ **Users can now:**
- Register and login immediately
- See clear instructions
- Verify email at their convenience
- Not get blocked by confusing verification flow

✅ **You can:**
- Track verification status
- Restrict features for unverified users
- Send verification reminders
- Provide better user experience
