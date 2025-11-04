# Troubleshooting Guide

## Common Issues and Solutions

### 1. ModuleNotFoundError: No module named 'Crypto'

**Error:**
```
ModuleNotFoundError: No module named 'Crypto'
```

**Solution:**
```bash
# Install pycryptodome in virtual environment
cd "E:\Developer\Back-END\Fastapi\E-commerce"
.venv\Scripts\python.exe -m pip install pycryptodome
```

**If pip is missing:**
```bash
# First, ensure pip is installed
.venv\Scripts\python.exe -m ensurepip --default-pip

# Then install pycryptodome
.venv\Scripts\python.exe -m pip install pycryptodome
```

---

### 2. Application Won't Start

**Check:**
1. Virtual environment activated
2. All dependencies installed
3. .env file configured

**Solution:**
```bash
# Install all dependencies
.venv\Scripts\python.exe -m pip install -r requirements.txt

# Test import
.venv\Scripts\python.exe -c "from app.main import app; print('OK')"
```

---

### 3. Database Connection Error

**Error:**
```
Can't connect to MySQL server
```

**Solution:**
Check `.env` file:
```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=cms_db
```

Make sure MySQL is running:
```bash
# Check MySQL status
mysql -u root -p
```

---

### 4. ABA PayWay Configuration Error

**Error:**
```
ValidationError: ABA_PAYWAY_MERCHANT_ID is required
```

**Solution:**
Add to `.env` file (copy from `.env.example`):
```env
ABA_PAYWAY_MERCHANT_ID=ec462423
ABA_PAYWAY_PUBLIC_KEY=1fd5c1490c05370dd74af1e22a4d4ef9dab6086a
# ... (other ABA PayWay settings)
```

---

### 5. Port Already in Use

**Error:**
```
[Errno 10048] Address already in use
```

**Solution:**
```bash
# Use different port
uvicorn app.main:app --port 8001

# Or kill process on port 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

---

### 6. CORS Error in Browser

**Error:**
```
CORS policy: No 'Access-Control-Allow-Origin'
```

**Solution:**
Update `ALLOWED_ORIGINS` in `.env`:
```env
ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:8000"]
```

---

### 7. Email Not Sending

**Check:**
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password  # Use App Password, not regular password
```

**For Gmail:**
1. Enable 2-factor authentication
2. Generate App Password
3. Use App Password in .env

---

### 8. Stock Not Reducing

**Verify:**
1. Order placed successfully
2. Payment completed (if using payment gateway)
3. Check inventory table

**Debug:**
```bash
# Check order
GET /api/orders/{order_id}

# Check inventory
GET /api/inventory

# Check audit logs
GET /api/audit-logs
```

---

## Quick Verification Commands

### Test Everything Works:

```bash
# 1. Import test
.venv\Scripts\python.exe -c "from app.main import app; print('✓ App loads')"

# 2. Database test
.venv\Scripts\python.exe -c "from app.database import engine; engine.connect(); print('✓ Database connected')"

# 3. Routes test
.venv\Scripts\python.exe -c "from app.main import app; print(f'✓ {len(app.routes)} routes registered')"
```

### Check Service Status:

```bash
# Start server in test mode
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --log-level debug
```

Visit http://localhost:8000/docs to see all endpoints

---

## Dependencies Checklist

### Required Packages:

- [ ] fastapi
- [ ] uvicorn
- [ ] sqlalchemy
- [ ] pymysql
- [ ] alembic
- [ ] pydantic
- [ ] python-jose
- [ ] passlib
- [ ] bcrypt
- [ ] httpx
- [ ] pycryptodome ⭐ (for payment)

### Install All:
```bash
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

---

## Environment Variables Checklist

### Minimal Required:

```env
SECRET_KEY="your-32-char-secret"
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=cms_db
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

### For Payment:

```env
ABA_PAYWAY_MERCHANT_ID=ec462423
ABA_PAYWAY_PUBLIC_KEY=1fd5c1490c05370dd74af1e22a4d4ef9dab6086a
# ... (other keys in .env.example)
```

---

## Getting Help

### Log Files:

Check `logs/` directory for error logs

### Debug Mode:

```bash
# Run with debug logging
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --log-level debug
```

### API Documentation:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Test Endpoints:

```bash
# Health check
curl http://localhost:8000/

# List products
curl http://localhost:8000/api/products

# Check inventory
curl http://localhost:8000/api/inventory
```

---

**Last Updated:** 2025-11-02
