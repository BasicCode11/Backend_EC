from fastapi import APIRouter, Depends , HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta , datetime , timezone
from sqlalchemy.orm import Session
import uuid
from app.database import get_db
from app.models.user import User
from app.models.role import Role
from app.services.auth_service import AuthService
from app.schemas.auth import (
    LoginRequest, 
    LoginResponse, 
    UserResponse, 
    CustomerRegistration,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ResendVerificationRequest,
    MessageResponse
)
from app.core.config import settings
from app.core.security import create_access_token , oauth2_scheme , decode_access_token , get_token_data, hash_password
from app.deps.auth import get_current_user

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = AuthService.authenticate_user(db, request.email, request.password)

    access_token = AuthService.create_user_access_token(user)
    refresh_token = None
    # Optional refresh token
    if settings.REFRESH_TOKEN_ENABLED:
        refresh_token = AuthService.create_user_access_token(user, expire_delta=None)

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        refresh_token=refresh_token,
        user=UserResponse.from_orm(user)
    )


@router.post("/refresh", response_model=LoginResponse)
def refresh_token(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    # Re-issue a fresh 1-day token if user is still within idle window
    token_data = decode_access_token(token)
    user = db.query(User).filter(User.id == token_data.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    # This endpoint also bumps last activity
    user.last_login_at = datetime.now(timezone.utc)
    db.add(user)
    db.commit()

    new_token = AuthService.create_user_access_token(user)
    return LoginResponse(
        access_token=new_token,
        token_type="bearer",
        refresh_token=None,
        user=UserResponse.from_orm(user)
    )


@router.post("/logout")
def logout(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    token_data = decode_access_token(token)
    AuthService.logout_user(db, token_data)
    return {"message": "Successfully logged out"}
    

@router.post("/register", response_model=UserResponse)
def register_customer(request: CustomerRegistration, db: Session = Depends(get_db)):
    return AuthService.register_customer(db, request)
    

@router.get("/me", response_model=UserResponse)
def get_current_user_endpoint(user: User = Depends(get_current_user)):
    return user


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Request password reset - sends email with reset link"""
    AuthService.request_password_reset(db, request.email)
    return MessageResponse(
        message="If the email exists, a password reset link has been sent"
    )


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset password using token from email"""
    AuthService.reset_password(db, request.token, request.new_password)
    return MessageResponse(message="Password has been reset successfully")


@router.get("/verify-email/{token}", response_model=MessageResponse)
def verify_email(token: str, db: Session = Depends(get_db)):
    """Verify user email with token from email link"""
    AuthService.verify_email(db, token)
    return MessageResponse(message="Email verified successfully")


@router.post("/resend-verification", response_model=MessageResponse)
def resend_verification(request: ResendVerificationRequest, db: Session = Depends(get_db)):
    """Resend email verification link"""
    AuthService.resend_verification_email(db, request.email)
    return MessageResponse(message="Verification email has been sent")

