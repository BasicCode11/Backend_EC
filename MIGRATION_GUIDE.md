# 🚀 Database Migration Guide

This guide will help you set up the complete e-commerce authentication and user management system.

## 📋 What Gets Created

### 🔑 Permissions (60+ permissions)

- **User Management**: create, read, update, delete, list, search
- **Role Management**: create, read, update, delete, list
- **Permission Management**: create, read, update, delete, list
- **Product Management**: create, read, update, delete, list, search
- **Category Management**: create, read, update, delete, list
- **Order Management**: create, read, update, delete, list, search, status_update
- **Shopping Cart**: create, read, update, delete, add_item, remove_item, clear
- **Payment Management**: create, read, update, delete, list
- **Inventory Management**: create, read, update, delete, list, adjust
- **Review Management**: create, read, update, delete, list
- **Discount Management**: create, read, update, delete, list
- **Analytics & Reports**: read, generate, export
- **System Administration**: settings, logs, backup, maintenance

### 👥 Roles (2 roles)

**1. Admin Role**

- Full system access
- All user management permissions
- All product and order management
- All system administration permissions

**2. Customer Role**

- Shopping cart management
- Order creation and viewing
- Product browsing (read-only)
- Review management
- Payment creation

### 👤 Users (3 users)

**1. Admin User**

- Email: `admin@example.com`
- Password: `admin123`
- Name: Admin User
- Role: Admin

**2. Customer 1**

- Email: `customer1@example.com`
- Password: `customer123`
- Name: John Doe
- Role: Customer

**3. Customer 2**

- Email: `customer2@example.com`
- Password: `customer123`
- Name: Jane Smith
- Role: Customer

## 🚀 How to Run Migration

### Option 1: Automated Migration (Recommended)

```bash
python run_migration.py
```

### Option 2: Manual Migration

```bash
python app/seed/migrations.py
```

### Option 3: Test Migration

```bash
python test_migration.py
```

## 🧪 Testing the System

### 1. Start the FastAPI Server

```bash
uvicorn app.main:app --reload
```

### 2. Test API Endpoints

```bash
python test_api.py
```

### 3. Manual Testing

**Admin Login:**

```bash
curl -X POST "http://localhost:8000/api/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "admin123"}'
```

**Customer Login:**

```bash
curl -X POST "http://localhost:8000/api/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "customer1@example.com", "password": "customer123"}'
```

**Customer Registration:**

```bash
curl -X POST "http://localhost:8000/api/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newcustomer@example.com",
    "password": "password123",
    "first_name": "New",
    "last_name": "Customer",
    "phone": "+1234567893"
  }'
```

## 📚 API Endpoints

### Authentication

- `POST /api/login` - User login
- `POST /api/logout` - User logout
- `POST /api/register` - Customer registration
- `GET /api/me` - Current user info

### Admin User Management

- `GET /api/user` - List all users
- `GET /api/user/{user_id}` - Get specific user
- `POST /api/user` - Create new user
- `PUT /api/user/{user_id}` - Update user
- `DELETE /api/user/{user_id}` - Delete user
- `POST /api/user/search` - Search users
- `GET /api/user/stats/count` - User statistics

## 🔒 Security Features

- **JWT Token Authentication**
- **Role-Based Access Control**
- **Permission-Based Endpoint Protection**
- **Password Hashing with bcrypt**
- **Token Blacklisting for Secure Logout**
- **Email Verification System Ready**

## 🎯 Next Steps

1. **Run the migration** to create the initial data
2. **Start the FastAPI server** to test the endpoints
3. **Test the authentication** with the provided users
4. **Implement additional e-commerce features** using the permission system

## 🐛 Troubleshooting

### Common Issues

**1. Import Errors**

- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Check that all model files exist and are properly imported

**2. Database Connection Issues**

- Verify your database configuration in `app/core/config.py`
- Ensure your database server is running

**3. Permission Errors**

- Check that the migration completed successfully
- Verify that roles and permissions were created

**4. Authentication Issues**

- Ensure JWT secret key is properly configured
- Check that user passwords are correctly hashed

### Getting Help

If you encounter issues:

1. Check the console output for error messages
2. Run `python test_migration.py` to verify the migration
3. Check the FastAPI documentation at `http://localhost:8000/docs`

## 🎉 Success!

Once the migration is complete, you'll have:

- ✅ 60+ comprehensive permissions
- ✅ 2 roles with proper access control
- ✅ 3 pre-created users for testing
- ✅ Complete authentication system
- ✅ Admin user management system
- ✅ Customer registration system

Your e-commerce backend is ready for development! 🚀
