# Password Reset with Email Verification Code

## Overview

The password reset flow now uses a **6-digit verification code** sent via email for enhanced security. This replaces the old token-based link approach.

## Changes Made

### 1. Database Model Updates
**File:** `app/models/password_reset_token.py`

Added new fields:
- `verification_code` (String, 6 digits) - The code sent to user's email
- `code_verified` (Boolean) - Tracks if code has been verified

New methods:
- `is_code_valid` - Checks if code can be verified
- `mark_code_verified()` - Marks code as verified after successful verification

### 2. Email Service Updates
**File:** `app/services/email_service.py`

Updated `send_password_reset_email()` to:
- Accept `verification_code` instead of `reset_token`
- Send 6-digit code in email body
- Code expires in **15 minutes** (reduced from 1 hour)

### 3. Auth Service Updates
**File:** `app/services/auth_service.py`

**New method:** `verify_reset_code(email, code)`
- Validates the 6-digit code
- Returns a reset_token if code is valid
- Marks code as verified

**Updated method:** `request_password_reset(email)`
- Generates random 6-digit code
- Code expires in 15 minutes
- Sends code via email

**Updated method:** `reset_password(reset_token, new_password)`
- Now requires reset_token from verified code
- Checks if code was verified before allowing password reset

### 4. API Schemas Updates
**File:** `app/schemas/auth.py`

**New schemas:**
```python
class VerifyResetCodeRequest(BaseModel):
    email: str
    code: str  # 6-digit code

class VerifyResetCodeResponse(BaseModel):
    message: str
    reset_token: str  # Use this for password reset
```

**Updated schema:**
```python
class ResetPasswordRequest(BaseModel):
    reset_token: str  # Changed from 'token'
    new_password: str
```

### 5. API Endpoints Updates
**File:** `app/routers/auth_router.py`

#### New Endpoint: `/api/verify-reset-code`
Verifies the 6-digit code and returns reset_token

#### Updated Endpoints:
- `/api/forgot-password` - Sends 6-digit code instead of link
- `/api/reset-password` - Requires reset_token from code verification

---

## Password Reset Flow

### Step 1: Request Password Reset
**Endpoint:** `POST /api/forgot-password`

**Request:**
```json
{
  "email": "user@example.com"
}
```

**Response:**
```json
{
  "message": "If the email exists, a verification code has been sent to your email"
}
```

**Email Sent:**
```
Subject: Password Reset Verification Code

Hello,

We received a request to reset your password. Use the verification code below to confirm:

Verification Code: 123456

This code will expire in 15 minutes.

If you didn't request a password reset, please ignore this email.

For security reasons, never share this code with anyone.

Best regards,
Your E-commerce Team
```

---

### Step 2: Verify Code
**Endpoint:** `POST /api/verify-reset-code`

**Request:**
```json
{
  "email": "user@example.com",
  "code": "123456"
}
```

**Success Response:**
```json
{
  "message": "Code verified successfully. Use the reset_token to set new password.",
  "reset_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Error Responses:**

Code Invalid:
```json
{
  "detail": "Invalid verification code"
}
```

Code Expired:
```json
{
  "detail": "Verification code has expired or already been used"
}
```

---

### Step 3: Reset Password
**Endpoint:** `POST /api/reset-password`

**Request:**
```json
{
  "reset_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "new_password": "NewSecurePassword123"
}
```

**Success Response:**
```json
{
  "message": "Password has been reset successfully"
}
```

**Error Responses:**

Token Not Verified:
```json
{
  "detail": "Please verify your code first"
}
```

Token Expired:
```json
{
  "detail": "Reset token has expired or already been used"
}
```

---

## Frontend Implementation Example

### React/TypeScript Example

```typescript
// Step 1: Request reset code
const requestPasswordReset = async (email: string) => {
  try {
    const response = await fetch('/api/forgot-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email })
    });
    
    const data = await response.json();
    console.log(data.message);
    // Show: "Check your email for verification code"
  } catch (error) {
    console.error('Error:', error);
  }
};

// Step 2: Verify code
const verifyResetCode = async (email: string, code: string) => {
  try {
    const response = await fetch('/api/verify-reset-code', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, code })
    });
    
    const data = await response.json();
    const { reset_token } = data;
    
    // Save reset_token for next step
    sessionStorage.setItem('reset_token', reset_token);
    return reset_token;
  } catch (error) {
    console.error('Invalid code:', error);
    throw error;
  }
};

// Step 3: Reset password
const resetPassword = async (resetToken: string, newPassword: string) => {
  try {
    const response = await fetch('/api/reset-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        reset_token: resetToken, 
        new_password: newPassword 
      })
    });
    
    const data = await response.json();
    console.log(data.message);
    // Redirect to login page
  } catch (error) {
    console.error('Error resetting password:', error);
    throw error;
  }
};

// Complete flow
const handlePasswordReset = async () => {
  const email = 'user@example.com';
  const code = '123456'; // From user input
  const newPassword = 'NewSecurePassword123';
  
  // Step 1: Request code
  await requestPasswordReset(email);
  
  // Step 2: User enters code, verify it
  const resetToken = await verifyResetCode(email, code);
  
  // Step 3: Reset password
  await resetPassword(resetToken, newPassword);
};
```

---

## Security Features

1. **Short Expiry Time:** Codes expire in 15 minutes
2. **Single Use:** Code can only be verified once
3. **Rate Limiting:** 
   - 3 reset requests per hour per IP
   - 5 verification attempts per hour per IP
   - 5 password reset attempts per hour per IP
4. **Code Complexity:** Random 6-digit numeric code
5. **Two-Step Verification:** Code verification separate from password reset
6. **No Information Leakage:** Generic messages don't reveal if email exists

---

## Database Migration

Run the migration to add the new fields:

```bash
# Apply migration
alembic upgrade head

# If you need to rollback
alembic downgrade -1
```

---

## Testing

### Manual Test Flow

1. **Request Reset:**
```bash
curl -X POST http://localhost:8000/api/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com"}'
```

2. **Check Logs for Code:**
```
[EMAIL] Subject: Password Reset Verification Code
[EMAIL] Content:
Verification Code: 123456
```

3. **Verify Code:**
```bash
curl -X POST http://localhost:8000/api/verify-reset-code \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","code":"123456"}'
```

4. **Reset Password:**
```bash
curl -X POST http://localhost:8000/api/reset-password \
  -H "Content-Type: application/json" \
  -d '{
    "reset_token":"<token_from_step_3>",
    "new_password":"NewPassword123"
  }'
```

---

## Common Issues & Solutions

### Issue: Code expires too quickly
**Solution:** Update expiry time in `auth_service.py`:
```python
expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)  # Change from 15 to 30
```

### Issue: Not receiving emails
**Solution:** 
- Check application logs (development mode logs emails)
- In production, configure SMTP settings in `email_service.py`

### Issue: Code verification fails
**Solution:**
- Ensure code is exactly 6 digits
- Check if code has expired (15 minutes)
- Verify email address matches the one used in Step 1

---

## Future Enhancements

1. **SMS Option:** Add phone number verification as alternative
2. **Multiple Attempts Tracking:** Lock account after too many failed attempts
3. **Email Templates:** Use HTML email templates instead of plain text
4. **SMTP Integration:** Connect to SendGrid, AWS SES, or Mailgun
5. **Audit Logging:** Track all password reset attempts

---

## API Documentation

All endpoints are automatically documented at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
