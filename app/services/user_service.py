from typing import List, Optional
from sqlalchemy import select, or_
from sqlalchemy.orm import Session
from app.models.user import User
from app.core.security import hash_password, verify_password
from app.schemas.user import UserCreate, UserUpdate, UserSearchParams, UserSelfUpdate , UserProfileBundle , UserResponse , RoleOut , UserWithPerPage
from app.core.exceptions import ValidationError, ForbiddenException
import uuid
from app.schemas.address import AddressResponse, AddressCreate
from app.services.address_service import AddressService

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
    def search_users(db: Session, search_params: UserSearchParams) -> List[User]:
        """Search users with various filters"""
        return UserService.get_all(
            db=db,
            skip=search_params.skip,
            limit=search_params.limit,
            search_params=search_params
        )

    @staticmethod
    def create(db: Session, user_data: UserCreate, address_data: AddressCreate, created_by: User) -> User:
        if UserService.get_by_email(db, user_data.email):
            raise ValidationError("Email already exists")

        hashed_pw = hash_password(user_data.password)

        db_user = User(
            uuid=str(uuid.uuid4()),
            email=user_data.email,
            password_hash=hashed_pw,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            phone=user_data.phone,
            picture=user_data.picture,
            role_id=user_data.role_id,
            email_verified=True  # Admin created users are auto-verified
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # Create address for the user if provided
        if address_data:
            AddressService.create_for_user(db, db_user, address_data)
        
        return db_user

    @staticmethod
    def update(db: Session, user_id: int, user_data: UserUpdate, updated_by: User) -> User:
        db_user = UserService.get_by_id(db, user_id)
        if not db_user:
            raise ValidationError("User not found")

        update_data = user_data.dict(exclude_unset=True)
        if "password" in update_data:
            update_data["password_hash"] = hash_password(update_data["password"])
            del update_data["password"]

        for field, value in update_data.items():
            setattr(db_user, field, value)

        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def self_update(db: Session, user_id: int, user_data: UserSelfUpdate) -> User:
        db_user = UserService.get_by_id(db, user_id)
        if not db_user:
            raise ValidationError("User not found")
        if user_data.comfime_password and not verify_password(user_data.comfime_password, db_user.password_hash):
            raise ValidationError("Current password is incorrect")
        update_data = user_data.dict(exclude_unset=True)
        if "password" in update_data and update_data["password"]:
            update_data["password_hash"] = hash_password(update_data["password"])
            del update_data["password"]

        # Restrict fields to only allowed ones implicitly by schema
        for field, value in update_data.items():
            setattr(db_user, field, value)

        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def delete(db: Session, user_id: int, deleted_by: User) -> None:
        db_user = UserService.get_by_id(db, user_id)
        if not db_user:
            raise ValidationError("User not found")

        db.delete(db_user)
        db.commit()

    @staticmethod
    def authenticate(db: Session, email: str, password: str) -> Optional[User]:
        user = UserService.get_by_email(db, email)
        if not user or not verify_password(password, user.password_hash):
            return None
        return user

    @staticmethod
    def change_password(db: Session, user: User, current_password: str, new_password: str) -> bool:
        db_user = UserService.get_by_id(db, user.id)
        if not db_user or not verify_password(current_password, db_user.password_hash):
            raise ValidationError("Current password is incorrect")

        db_user.password_hash = hash_password(new_password)
        db.commit()
        db.refresh(db_user)
        return True

    @staticmethod
    def reset_password(db: Session, user_id: int, new_password: str) -> bool:
        user = UserService.get_by_id(db, user_id)
        if not user:
            raise ValidationError("User not found")

        user.password_hash = hash_password(new_password)
        db.commit()
        db.refresh(user)
        return True

    @staticmethod
    def get_user_count(db: Session, email_verified: Optional[bool] = None) -> int:
        query = db.query(User)
        if email_verified is not None:
            query = query.filter(User.email_verified == email_verified)
        return query.count()
