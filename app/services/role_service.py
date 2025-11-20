from fastapi import HTTPException, status
from typing import List, Optional
from sqlalchemy import select, delete
from sqlalchemy.orm import Session
from app.models.role import Role
from app.schemas.role import RoleCreate, RoleUpdate , RoleOut
from app.models.permission import Permission
from app.models.role_has_permision import role_has_permission
from app.services.audit_log_service import AuditLogService
from app.models.user import User
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
    def create(db: Session,  role_data: RoleCreate ,current_user: User,) -> RoleOut:
        """Create a new role."""
        existing = db.execute(select(Role).where(Role.name == role_data.name)).scalars().first()
        if existing:
            raise ValueError("Role with this name already exists")
        role = Role(name=role_data.name, description=role_data.description)
        if role_data.permission_ids:
            permissions = db.query(Permission).filter(
                Permission.id.in_(role_data.permission_ids)
            ).all()

            if not permissions and role_data.permission_ids:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Some permissions not found"
                )

            role.permissions = permissions

            
        db.add(role)
        db.commit()
        db.refresh(role)

        #audit log data 
        AuditLogService.log_create(
            db=db,
            user_id=current_user.id,
            entity_type="Role",
            entity_id=role.id,
            new_values={
                "name": role.name,
                "description": role.description
            }
        )
        return role
    
    @staticmethod
    def update(db: Session, role_id: int, role_data: RoleUpdate,current_user: User) -> Optional[Role]:
        """Update an existing role."""
        role = RoleService.get_by_id(db, role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role with id {role_id} not found"
            )
        #auth log old data 
        old_values = {
            "name": role.name,
            "description": role.description
        }
        if role_data.name is not None:
            role.name = role_data.name
        if role_data.description is not None:
            role.description = role_data.description

        if hasattr(role_data, 'permission_ids') and role_data.permission_ids is not None:
            permissions = db.query(Permission).filter(Permission.id.in_(role_data.permission_ids)).all()

            if not permissions and role_data.permission_ids:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Some permissions not found"
                )
            # Replace role permissions
            role.permissions = permissions
        #audit log new data 
        new_values = {
            "name": role_data.name,
            "description": role_data.description
        }
        
        db.commit()
        db.refresh(role)

        AuditLogService.log_update(
            db=db,
            user_id=current_user.id,
            entity_type="Role",
            entity_id=role.id,
            old_values=old_values,
            new_values=new_values
        )
        return role
    
    @staticmethod
    def delete(db: Session, role_id: int , current_user: User) -> bool:
        """Delete a role."""
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )
        user_count = db.query(User).filter(User.role_id == role_id).count()
        if user_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete role because it has assigned users."
            )
    
        #auth log old data 
        AuditLogService.log_delete(
            db=db,
            user_id=current_user.id,
            entity_type="Role",
            entity_id=role.id,
            old_values={
                "name": role.name,
                "description": role.description
            }
        )
        db.delete(role)
        db.commit()
        return {"message": f"Role '{role.name}' deleted successfully."}

    
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