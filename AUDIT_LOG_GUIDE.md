# Audit Log System Guide

## Overview
The audit log system tracks all important actions and changes in the application, providing a complete audit trail for compliance, debugging, and security monitoring.

## Features
- Track user actions (create, update, delete)
- Log authentication events (login, logout)
- Store old and new values for updates
- Capture IP address and user agent
- Flexible filtering and querying
- User activity reports
- Entity history tracking

## Database Schema

The `audit_logs` table contains:
- `id`: Primary key
- `user_id`: User who performed the action (nullable, SET NULL on user deletion)
- `action`: Type of action (CREATE, UPDATE, DELETE, LOGIN_SUCCESS, LOGIN_FAILED, LOGOUT)
- `entity_type`: Type of entity affected (User, Product, Order, etc.)
- `entity_id`: ID of the affected entity
- `entity_uuid`: UUID of the affected entity (if applicable)
- `changes`: JSON object with field-level changes
- `old_values`: JSON object with values before change
- `new_values`: JSON object with values after change
- `ip_address`: Client IP address
- `user_agent`: Client user agent string
- `description`: Human-readable description
- `created_at`: Timestamp of the action

## API Endpoints

### Get All Audit Logs (Admin)
```http
GET /api/audit-logs?page=1&limit=50&action=CREATE&entity_type=User
Authorization: Bearer <admin_token>
```

**Query Parameters:**
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 50, max: 200)
- `user_id`: Filter by user
- `action`: Filter by action type
- `entity_type`: Filter by entity type
- `entity_id`: Filter by entity ID
- `entity_uuid`: Filter by entity UUID
- `start_date`: Filter by start date
- `end_date`: Filter by end date

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "user_id": 4,
      "user_email": "admin@example.com",
      "user_name": "Admin User",
      "action": "CREATE",
      "entity_type": "User",
      "entity_id": 10,
      "entity_uuid": "550e8400-e29b-41d4-a716-446655440000",
      "new_values": {
        "email": "newuser@example.com",
        "first_name": "John",
        "last_name": "Doe"
      },
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0...",
      "description": "Created User with ID 10",
      "created_at": "2025-10-31T12:00:00Z"
    }
  ],
  "total": 150,
  "page": 1,
  "limit": 50
}
```

### Get Specific Audit Log
```http
GET /api/audit-logs/{log_id}
Authorization: Bearer <admin_token>
```

### Get User Activity
```http
GET /api/audit-logs/user/{user_id}?page=1&limit=50
Authorization: Bearer <admin_token>
```

### Get Entity History
```http
GET /api/audit-logs/entity/{entity_type}/{entity_id}?page=1&limit=50
Authorization: Bearer <admin_token>
```

Example:
```http
GET /api/audit-logs/entity/User/10
```

### Get My Activity (Current User)
```http
GET /api/me/activity?page=1&limit=50
Authorization: Bearer <user_token>
```

## Using Audit Logging in Your Code

### Method 1: Using the Service Layer Directly

```python
from app.services.audit_log_service import AuditLogService

# Log a create action
AuditLogService.log_create(
    db=db,
    user_id=current_user.id,
    entity_type="Product",
    entity_id=product.id,
    entity_uuid=product.uuid,
    new_values={"name": product.name, "price": product.price},
    ip_address="192.168.1.100",
    user_agent="Mozilla/5.0..."
)

# Log an update action
AuditLogService.log_update(
    db=db,
    user_id=current_user.id,
    entity_type="Product",
    entity_id=product.id,
    entity_uuid=product.uuid,
    old_values={"price": 100.00},
    new_values={"price": 120.00},
    changes={"price": {"old": 100.00, "new": 120.00}},
    ip_address="192.168.1.100",
    user_agent="Mozilla/5.0..."
)

# Log a delete action
AuditLogService.log_delete(
    db=db,
    user_id=current_user.id,
    entity_type="Product",
    entity_id=product.id,
    entity_uuid=product.uuid,
    old_values={"name": product.name, "price": product.price}
)
```

### Method 2: Using Helper Functions

```python
from app.utils.audit_helper import log_user_create, log_user_update, log_user_delete
from fastapi import Request

# In your route handler
@router.post("/user")
def create_user(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    new_user = UserService.create(db, user_data, current_user)
    
    # Log the action (helper automatically extracts IP and user agent)
    log_user_create(
        db=db,
        user_id=current_user.id,
        created_user_id=new_user.id,
        created_user_uuid=new_user.uuid,
        request=request
    )
    
    return new_user
```

### Method 3: Generic Entity Logging

```python
from app.utils.audit_helper import log_entity_action

# Log any action on any entity
log_entity_action(
    db=db,
    action="APPROVED",
    entity_type="Order",
    entity_id=order.id,
    user_id=current_user.id,
    entity_uuid=order.uuid,
    changes={"status": {"old": "pending", "new": "approved"}},
    description=f"Order {order.id} approved by {current_user.email}",
    request=request
)
```

## Integrating with Existing Services

Example: Adding audit logging to UserService

```python
class UserService:
    @staticmethod
    def create(db: Session, user_data: UserCreate, created_by: User) -> User:
        # ... existing create logic ...
        
        # Log the action
        AuditLogService.log_create(
            db=db,
            user_id=created_by.id,
            entity_type="User",
            entity_id=db_user.id,
            entity_uuid=db_user.uuid,
            new_values={
                "email": db_user.email,
                "first_name": db_user.first_name,
                "last_name": db_user.last_name,
                "role_id": db_user.role_id
            }
        )
        
        return db_user
    
    @staticmethod
    def update(db: Session, user_id: int, user_data: UserUpdate, updated_by: User) -> User:
        db_user = UserService.get_by_id(db, user_id)
        
        # Store old values
        old_values = {
            "email": db_user.email,
            "first_name": db_user.first_name,
            "last_name": db_user.last_name,
            "role_id": db_user.role_id
        }
        
        # ... perform update ...
        
        # Store new values
        new_values = {
            "email": db_user.email,
            "first_name": db_user.first_name,
            "last_name": db_user.last_name,
            "role_id": db_user.role_id
        }
        
        # Log the action
        AuditLogService.log_update(
            db=db,
            user_id=updated_by.id,
            entity_type="User",
            entity_id=db_user.id,
            entity_uuid=db_user.uuid,
            old_values=old_values,
            new_values=new_values
        )
        
        return db_user
```

## Permissions

To access audit logs, users need the `audit_logs:read` permission. Add this permission to admin roles:

```python
# In your role setup
admin_role = Role(name="admin")
audit_permission = Permission(name="audit_logs:read", description="View audit logs")
admin_role.permissions.append(audit_permission)
```

## Best Practices

1. **Log Important Actions**: Focus on actions that have security, compliance, or business implications
2. **Don't Log Sensitive Data**: Never log passwords, tokens, or other sensitive information
3. **Use Consistent Entity Types**: Use standard naming (User, Product, Order, etc.)
4. **Include Context**: Provide useful descriptions and store relevant old/new values
5. **Capture Client Info**: Always pass the `request` object to capture IP and user agent
6. **Performance**: Audit logging is lightweight but consider async logging for high-traffic endpoints
7. **Retention**: Plan for log retention and archiving policies

## Common Action Types

- `CREATE`: Entity was created
- `UPDATE`: Entity was updated
- `DELETE`: Entity was deleted
- `LOGIN_SUCCESS`: Successful authentication
- `LOGIN_FAILED`: Failed authentication attempt
- `LOGOUT`: User logged out
- `APPROVE`: Entity was approved
- `REJECT`: Entity was rejected
- `CANCEL`: Entity was cancelled
- `RESTORE`: Entity was restored
- Custom actions as needed

## Querying Examples

### Get all failed login attempts in the last 24 hours
```python
from datetime import datetime, timedelta

filters = AuditLogFilter(
    action="LOGIN_FAILED",
    start_date=datetime.now() - timedelta(days=1),
    page=1,
    limit=100
)
logs = AuditLogService.get_all(db, filters)
```

### Get all changes to a specific user
```python
filters = AuditLogFilter(
    entity_type="User",
    entity_id=10,
    page=1,
    limit=50
)
history = AuditLogService.get_all(db, filters)
```

### Get all actions by a specific admin
```python
filters = AuditLogFilter(
    user_id=admin_user_id,
    page=1,
    limit=100
)
activity = AuditLogService.get_all(db, filters)
```

## Troubleshooting

### Audit logs not being created
- Check database connection
- Verify the audit_logs table exists
- Ensure the logging code is being executed
- Check for transaction rollbacks

### Missing user information
- User might have been deleted (user_id will be NULL due to SET NULL constraint)
- User performed action before authentication (system actions)

### Performance issues
- Add indexes on frequently queried fields (already included)
- Consider archiving old logs
- Use pagination effectively
- Consider async logging for high-volume scenarios
