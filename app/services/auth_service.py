from datetime import timedelta, datetime, timezone
from fastapi import HTTPException, status
from typing import Optional
from sqlalchemy.orm import Session
from app.models.role import Role
from app.models.user import User
from app.core.config import settings
from app.schemas.auth import TokenData
from app.core.security import verify_password, create_access_token
from app.services.token_blacklist_service import TokenBlacklistService
from app.schemas.auth import CustomerRegistration
from app.core.security import hash_password
import uuid

class AuthService:

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> User:
        user = db.query(User).filter(User.email == email).first()
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return user
    

    @staticmethod
    def create_user_access_token(user: User, expire_delta: Optional[timedelta] = None) -> str:
        """Create access token for a user"""
        # Default: short-lived token (1 day) to pair with idle timeout checks
        expire = expire_delta if expire_delta is not None else timedelta(days=1)
        return create_access_token(
            data={
                "sub": user.email,
                "user_id": user.id,
                "uuid": user.uuid,
                "role_id": user.role_id,
            },
            expires_delta=expire
        )

    @staticmethod
    def register_customer(db: Session, customer_data: CustomerRegistration) -> User:
        existing_user = db.query(User).filter(User.email == customer_data.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        customer_role = db.query(Role).filter(Role.name == "customer").first()
        if not customer_role:
            customer_role = Role(name="customer", description="Default customer role")
            db.add(customer_role)
            db.commit()
            db.refresh(customer_role)

        hashed_password = hash_password(customer_data.password)
        new_user = User(
            uuid=str(uuid.uuid4()),
            email=customer_data.email,
            password_hash=hashed_password,
            first_name=customer_data.first_name,
            last_name=customer_data.last_name,
            phone=customer_data.phone,
            role_id=customer_role.id,
            email_verified=True
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    @staticmethod
    def logout_user(db: Session, token_data: TokenData):
        AuthService.verify_token_not_blacklisted(db, token_data.jti)
        expires = datetime.fromtimestamp(token_data.exp, tz=timezone.utc)
        TokenBlacklistService.blacklist_token(db, token_data.jti, expires)
