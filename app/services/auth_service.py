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
from app.services.audit_log_service import AuditLogService
import uuid
import secrets

class AuthService:

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> User:
        user = db.query(User).filter(User.email == email).first()
        if not user or not verify_password(password, user.password_hash):
            # Log failed login attempt
            if user:
                AuditLogService.log_login(
                    db=db,
                    user_id=user.id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    success=False
                )
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Log successful login
        AuditLogService.log_login(
            db=db,
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            success=True
        )
        
        # Allow login even if email not verified (soft verification)
        # Frontend can show a banner: "Please verify your email"
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
                "token_type": "access"
            },
            expires_delta=expire
        )
    
    @staticmethod
    def create_user_refresh_token(user: User) -> str:
        """Create long-lived refresh token for a user"""
        expire = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        return create_access_token(
            data={
                "sub": user.email,
                "user_id": user.id,
                "uuid": user.uuid,
                "role_id": user.role_id,
                "token_type": "refresh"
            },
            expires_delta=expire
        )

    @staticmethod
    def register_customer(db: Session, customer_data: CustomerRegistration, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> User:
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
        
        # Log user registration
        AuditLogService.log_create(
            db=db,
            user_id=None,  # Self-registration, no authenticated user
            entity_type="User",
            entity_id=new_user.id,
            entity_uuid=new_user.uuid,
            new_values={
                "email": new_user.email,
                "first_name": new_user.first_name,
                "last_name": new_user.last_name,
                "role": "customer"
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Generate verification token and send email
        verification_token = AuthService.generate_verification_token(db, new_user)
        EmailService.send_verification_email(
            db=db,
            recipient_email=new_user.email,
            verification_token=verification_token.token
        )
        
        return new_user

    @staticmethod
    def logout_user(db: Session, token_data: TokenData, ip_address: Optional[str] = None, user_agent: Optional[str] = None):
        expires = datetime.fromtimestamp(token_data.exp, tz=timezone.utc)
        TokenBlacklistService.blacklist_token(db, token_data.jti, expires)
        
        # Log logout
        AuditLogService.log_logout(
            db=db,
            user_id=token_data.user_id,
            ip_address=ip_address,
            user_agent=user_agent
        )

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
    def request_password_reset(db: Session, email: str) -> None:
        """Request password reset - generates token and verification code, sends email"""
        user = db.query(User).filter(User.email == email).first()
        
        # For security, don't reveal if email exists
        if not user:
            raise HTTPException(
                status_code= status.HTTP_404_NOT_FOUND,
                detail="Email address not Found! Please Enter Current Email!"
            )
        
        # Invalidate any existing unused tokens
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used == False
        ).update({"used": True})
        db.commit()
        
        # Generate 6-digit verification code
        verification_code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        
        # Create new token (for backend tracking)
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)  # 15 minutes expiry
        
        reset_token = PasswordResetToken(
            user_id=user.id,
            token=token,
            verification_code=verification_code,
            expires_at=expires_at
        )
        db.add(reset_token)
        db.commit()
        
        # Send email with verification code
        EmailService.send_password_reset_email(
            db=db,
            recipient_email=user.email,
            verification_code=verification_code
        )

    @staticmethod
    def verify_reset_code(db: Session, email: str, code: str) -> str:
        """Verify reset code and return reset token if valid"""
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email address not found"
            )
        
        # Find the most recent valid reset token for this user
        reset_token = db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.verification_code == code,
            PasswordResetToken.used == False
        ).order_by(PasswordResetToken.created_at.desc()).first()
        
        if not reset_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification code"
            )
        
        if not reset_token.is_code_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification code has expired or already been used"
            )
        
        # Mark code as verified
        reset_token.mark_code_verified()
        db.commit()
        
        # Return the token for password reset
        return reset_token.token
    
    @staticmethod
    def reset_password(db: Session, reset_token: str, new_password: str) -> User:
        """Reset password with verified token"""
        token_record = db.query(PasswordResetToken).filter(
            PasswordResetToken.token == reset_token
        ).first()
        
        if not token_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reset token"
            )
        
        # Check if code was verified
        if not token_record.code_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please verify your code first"
            )
        
        if not token_record.is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reset token has expired or already been used"
            )
        
        # Mark token as used
        token_record.mark_as_used()
        
        # Update user password
        user = db.query(User).filter(User.id == token_record.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user.password_hash = hash_password(new_password)
        db.commit()
        db.refresh(user)
        
        # Log password reset
        AuditLogService.create_log(
            db=db,
            user_id=user.id,
            action="PASSWORD_RESET",
            entity_type="User",
            entity_id=user.id,
            entity_uuid=user.uuid,
            description="User password was reset via email verification"
        )
        
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
