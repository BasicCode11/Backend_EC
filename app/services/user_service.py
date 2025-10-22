from typing import List, Optional
from sqlalchemy import select, or_
from sqlalchemy.orm import Session
from app.models.user import User
from app.core.security import hash_password, verify_password
from app.schemas.user import UserCreate, UserUpdate, UserSearchParams, UserSelfUpdate
from app.core.exceptions import ValidationError, ForbiddenException
import uuid

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
        skip: int = 0,
        limit: int = 100,
        role_id: Optional[int] = None,
        email_verified: Optional[bool] = None,
        search_params: Optional[UserSearchParams] = None,
    ) -> List[User]:
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
        if email_verified is not None:
            query = query.filter(User.email_verified == email_verified)
            
        return query.offset(skip).limit(limit).all()

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
    def create(db: Session, user_data: UserCreate, created_by: User) -> User:
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
            role_id=user_data.role_id,
            email_verified=True  # Admin created users are auto-verified
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
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
