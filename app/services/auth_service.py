from datetime import timedelta, datetime, timezone
from fastapi import HTTPException, status
from typing import Optional
from sqlalchemy.orm import Session
from app.models.role import Role
from app.models.user import User
from app.models.password_reset_token import PasswordResetToken
from app.models.email_verification_token import EmailVerificationToken
from app.core.config import settings
from app.schemas.auth import TokenData
from app.core.security import verify_password, create_access_token
from app.services.token_blacklist_service import TokenBlacklistService
from app.schemas.auth import CustomerRegistration
from app.core.security import hash_password
from app.services.email_service import EmailService
import uuid
import secrets

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
            email_verified=False  # Changed to False - user must verify email
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Generate verification token and send email
        verification_token = AuthService.generate_verification_token(db, new_user)
        EmailService.send_verification_email(
            db=db,
            recipient_email=new_user.email,
            verification_token=verification_token.token
        )
        
        return new_user

    @staticmethod
    def logout_user(db: Session, token_data: TokenData):
        expires = datetime.fromtimestamp(token_data.exp, tz=timezone.utc)
        TokenBlacklistService.blacklist_token(db, token_data.jti, expires)

    @staticmethod
    def generate_verification_token(db: Session, user: User) -> EmailVerificationToken:
        """Generate email verification token for user"""
        # Invalidate any existing unused tokens
        db.query(EmailVerificationToken).filter(
            EmailVerificationToken.user_id == user.id,
            EmailVerificationToken.used == False
        ).update({"used": True})
        db.commit()

        # Create new token
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
        
        verification_token = EmailVerificationToken(
            user_id=user.id,
            token=token,
            expires_at=expires_at
        )
        db.add(verification_token)
        db.commit()
        db.refresh(verification_token)
        
        return verification_token

    @staticmethod
    def verify_email(db: Session, token: str) -> User:
        """Verify user email with token"""
        verification_token = db.query(EmailVerificationToken).filter(
            EmailVerificationToken.token == token
        ).first()
        
        if not verification_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification token"
            )
        
        if not verification_token.is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification token has expired or already been used"
            )
        
        # Mark token as used
        verification_token.mark_as_used()
        
        # Update user email_verified status
        user = db.query(User).filter(User.id == verification_token.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user.email_verified = True
        db.commit()
        db.refresh(user)
        
        return user

    @staticmethod
    def request_password_reset(db: Session, email: str) -> None:
        """Request password reset - generates token and sends email"""
        user = db.query(User).filter(User.email == email).first()
        
        # For security, don't reveal if email exists
        if not user:
            return
        
        # Invalidate any existing unused tokens
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used == False
        ).update({"used": True})
        db.commit()
        
        # Create new token
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        
        reset_token = PasswordResetToken(
            user_id=user.id,
            token=token,
            expires_at=expires_at
        )
        db.add(reset_token)
        db.commit()
        
        # Send email
        EmailService.send_password_reset_email(
            db=db,
            recipient_email=user.email,
            reset_token=token
        )

    @staticmethod
    def reset_password(db: Session, token: str, new_password: str) -> User:
        """Reset password with token"""
        reset_token = db.query(PasswordResetToken).filter(
            PasswordResetToken.token == token
        ).first()
        
        if not reset_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reset token"
            )
        
        if not reset_token.is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reset token has expired or already been used"
            )
        
        # Mark token as used
        reset_token.mark_as_used()
        
        # Update user password
        user = db.query(User).filter(User.id == reset_token.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user.password_hash = hash_password(new_password)
        db.commit()
        db.refresh(user)
        
        # Send confirmation email
        EmailService.send_password_changed_notification(
            db=db,
            recipient_email=user.email
        )
        
        return user

    @staticmethod
    def resend_verification_email(db: Session, email: str) -> None:
        """Resend verification email"""
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if user.email_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is already verified"
            )
        
        # Generate new token
        verification_token = AuthService.generate_verification_token(db, user)
        
        # Send email
        EmailService.send_verification_email(
            db=db,
            recipient_email=user.email,
            verification_token=verification_token.token
        )
