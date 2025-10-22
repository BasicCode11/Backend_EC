
from typing import List, Optional
from sqlalchemy import select, delete
from sqlalchemy.orm import Session
from app.models.role import Role
from app.models.permission import Permission
from app.models.role_has_permision import role_has_permission

class RoleService:
    """Service layer for role operations."""
    @staticmethod
    def get_by_id(db: Session, role_id: int) -> Optional[Role]:
        """Get role by ID."""
        return db.get(Role, role_id)
    
    @staticmethod
    def get_by_name(db: Session, name: str) -> Optional[Role]:
        """Get role by name."""
        stmt = select(Role).where(Role.name == name)
        return db.execute(stmt).scalars().first()
    
    @staticmethod
    def get_all(db: Session) -> List[Role]:
        """Get all roles."""
        return db.execute(select(Role)).scalars().all()
    

    @staticmethod
    def create(db: Session, name: str, description: Optional[str] = None) -> Role:
        """Create a new role."""
        existing = db.execute(select(Role).where(Role.name == name)).scalars().first()
        if existing:
            raise ValueError("Role with this name already exists")
        role = Role(name=name, description=description)

        db.add(role)
        db.commit()
        db.refresh(role)
        return role
    
    @staticmethod
    def update(db: Session, role_id: int, name: str, description: Optional[str] = None) -> Optional[Role]:
        """Update an existing role."""
        role = db.get(Role, role_id)
        if not role:
            return None
        
        if name is not None:
            role.name = name
        if description is not None:
            role.description = description

        db.commit()
        db.refresh(role)
        return role
    
    @staticmethod
    def delete(db: Session, role_id: int) -> bool:
        """Delete a role."""
        role = db.get(Role, role_id)
        if not role:
            return
        
        db.delete(role)
        db.commit()
    
    @staticmethod
    def assign_permissions(db: Session, role_id: int, permission_ids: List[int]) -> bool:
        """Assign permissions to a role."""
        role = db.get(Role, role_id)
        if not role:
            return False
        
        permissions = db.execute(
            select(Permission).where(Permission.id.in_(permission_ids))
        ).scalars().all()

        if len(permissions) != len(permission_ids):
            raise ValueError("One or more permissions not found")
        
        db.execute(
            delete(role_has_permission).where(role_has_permission.c.role_id == role_id)
        )

        for permission_id in permission_ids:
            db.execute(
                role_has_permission.insert().values(role_id=role_id, permission_id=permission_id)
            )

        db.commit()
        return True
    
    @staticmethod
    def get_permissions(db: Session, role_id: int) -> List[Permission]:
        """Get permissions assigned to a role."""
        role = db.get(Role, role_id)
        if not role:
            return []
        return role.permissions
    
    @staticmethod
    def remove_permission(db: Session, role_id: int, permission_id: int) -> bool:
        """Remove a specific permission from a role."""
        result = db.execute(
            delete(role_has_permission).where(
                role_has_permission.c.role_id == role_id,
                role_has_permission.c.permission_id == permission_id
            )
        )
        db.commit()
        return result.rowcount > 0
