from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session , selectinload
from app.models.user import User
from app.core.security import hash_password
from app.schemas.user import UserCreate, UserUpdate, UserSearchParams , UserProfileBundle , UserResponse , RoleOut , UserWithPerPage
from app.core.exceptions import ValidationError
import uuid
from app.schemas.address import AddressResponse, AddressCreate , AddressUpdate
from app.services.address_service import AddressService
from app.services.audit_log_service import AuditLogService
from app.services.file_service import LogoUpload
class UserService:
    """Service layer for user operations."""

    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email)
        return db.execute(stmt).scalars().first()

    @staticmethod
    def get_by_id(db: Session, user_id: int) -> Optional[User]:
        return db.get(User, user_id)
    
    @staticmethod
    def get_with_addresses(db: Session, user_id: int) -> Optional[User]:
        stmt = (
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.addresses))
        )
        return db.execute(stmt).scalars().first()

    

    @staticmethod
    def get_all(
        db: Session,
        page: int = 1,
        limit: int = 100,
        role_id: Optional[int] = None,
        search_params: Optional[UserSearchParams] = None,
    ) -> dict:  
        query = db.query(User)
    
        if search_params:
            if search_params.email:
                query = query.filter(User.email.ilike(f"%{search_params.email}%"))
            if search_params.first_name:
                query = query.filter(User.first_name.ilike(f"%{search_params.first_name}%"))
            if search_params.last_name:
                query = query.filter(User.last_name.ilike(f"%{search_params.last_name}%"))
            if search_params.role_id:
                query = query.filter(User.role_id == search_params.role_id)
            if search_params.email_verified is not None:
                query = query.filter(User.email_verified == search_params.email_verified)
    
        if role_id is not None:
            query = query.filter(User.role_id == role_id)
    
        total = query.count()
        users = query.offset((page - 1) * limit).limit(limit).all()
    
        # Transform User objects to UserProfileBundle objects
        user_bundles = []
        for user in users:
            role_data = RoleOut(
                id=user.role.id,
                name=user.role.name
            )
            user_response = UserResponse(
                id=user.id, 
                uuid=user.uuid,
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                role=role_data,
                phone=user.phone,
                picture=user.picture,
                email_verified=user.email_verified,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
        
            # Convert addresses to AddressResponse objects
            address_responses = []
            for address in user.addresses:
                address_response = AddressResponse(
                    id=address.id,
                    user_id=address.user_id,
                    address_type=address.address_type,
                    label=address.label,
                    recipient_name=address.recipient_name,
                    company=address.company,
                    street_address=address.street_address,
                    apartment_suite=address.apartment_suite,
                    city=address.city,
                    state=address.state,
                    country=address.country,
                    postal_code=address.postal_code,
                    longitude=address.longitude,
                    latitude=address.latitude,
                    is_default=address.is_default,
                    is_active=address.is_active,
                    created_at=address.created_at,
                    updated_at=address.updated_at
                )
                address_responses.append(address_response)
        
            user_bundle = UserProfileBundle(
                user=user_response,
                addresses=address_responses
            )
            user_bundles.append(user_bundle)
    
        return UserWithPerPage(
            item=user_bundles,
            total=total,
            page=page,
            limit=limit
        )
          


    @staticmethod
    def create(db: Session, user_data: UserCreate, address_data: AddressCreate, created_by: User , picture: Optional[str] = None) -> User:
        if UserService.get_by_email(db, user_data.email):
            raise ValidationError("Email already exists")

        hashed_pw = hash_password(user_data.password)

        picture_url = None
        picture__url_public_id = None

        if picture:
            cloud = LogoUpload._save_image(picture)
            picture_url = cloud["url"]
            picture__url_public_id = cloud["public_id"]

        
        db_user = User(
            uuid=str(uuid.uuid4()),
            email=user_data.email,
            password_hash=hashed_pw,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            phone=user_data.phone,
            picture=picture_url,
            picture_public_id = picture__url_public_id,
            role_id=user_data.role_id,
            email_verified=True  # Admin created users are auto-verified
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # Create address for the user if provided
        if address_data:
            AddressService.create_for_user(db, db_user, address_data)
        
        # Log user creation
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
                "role_id": db_user.role_id,
                "phone": db_user.phone
            }
        )
        
        return db_user

    @staticmethod
    def update(db: Session, user_id: int, user_data: UserUpdate, address_data: AddressUpdate,updated_by: User , picture: Optional[str] = None) -> User:
        db_user = UserService.get_by_id(db, user_id)
        if not db_user:
            raise ValidationError("User not found")
        
        if picture:
            # Delete old image if exists
            if db_user.picture_public_id:
                LogoUpload._delete_logo(db_user.picture_public_id)

            # Upload new image to Cloudinary
            cloud = LogoUpload._save_image(picture)
            db_user.picture = cloud["url"]
            db_user.picture_public_id = cloud["public_id"]


        # Store old values for audit
        old_values = {
            "email": db_user.email,
            "first_name": db_user.first_name,
            "last_name": db_user.last_name,
            "role_id": db_user.role_id,
            "phone": db_user.phone,
            "picture": db_user.picture,
            "email_verified": db_user.email_verified
        }

        for field, value in user_data.dict(exclude_unset=True).items():
            setattr(db_user, field, value)

        db.commit()
        db.refresh(db_user)
        
        if address_data:
            user_address = AddressService.list_for_user(db , user_id)
            if user_address:
                AddressService.update_for_user(db, user_id, address_data)

        # Store new values for audit
        new_values = {
            "email": db_user.email,
            "first_name": db_user.first_name,
            "last_name": db_user.last_name,
            "role_id": db_user.role_id,
            "phone": db_user.phone,
            "picture": db_user.picture,
            "email_verified": db_user.email_verified
        }
        
        # Log user update
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
    

    @staticmethod
    def delete(db: Session, user_id: int, deleted_by: User) -> None:
        db_user = UserService.get_by_id(db, user_id)
        if not db_user:
            raise ValidationError("User not found")
        
        # Store user info before deletion
        old_values = {
            "email": db_user.email,
            "first_name": db_user.first_name,
            "last_name": db_user.last_name,
            "role_id": db_user.role_id
        }
        user_uuid = db_user.uuid
        if db_user.picture:
            LogoUpload._delete_logo(db_user.picture)

        db.delete(db_user)
        db.commit()
        
        db_address = AddressService.get_for_user(db, user_id)
        if db_address:
            AddressService.delete_for_user(db, db_address.id)

        # Log user deletion
        AuditLogService.log_delete(
            db=db,
            user_id=deleted_by.id,
            entity_type="User",
            entity_id=user_id,
            entity_uuid=user_uuid,
            old_values=old_values
        )

