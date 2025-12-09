from fastapi import APIRouter, Depends , HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta , datetime , timezone
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
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
    VerifyResetCodeRequest,
    VerifyResetCodeResponse,
    ResetPasswordRequest,
    MessageResponse
)
from app.core.config import settings
from app.core.security import create_access_token , oauth2_scheme , decode_access_token , get_token_data, hash_password
from app.deps.auth import get_current_user

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("/login")
@limiter.limit("5/minute")  # Max 5 login attempts per minute
def login(request: Request, login_req: LoginRequest, db: Session = Depends(get_db)):
    """
    Login with email and password.
    
    Returns:
    - access_token: Short-lived token (1 day) for API requests
    - refresh_token: Long-lived token (30 days) to get new access tokens
    
    Note: You can login even if email is not verified.
    Some features may be limited until email verification is complete.
    """
    # Extract client info
    ip_address = request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or request.headers.get("X-Real-IP", "") or (request.client.host if request.client else None)
    user_agent = request.headers.get("User-Agent")
    
    user = AuthService.authenticate_user(db, login_req.email, login_req.password, ip_address, user_agent)

    # Create access token (1 day)
    access_token = AuthService.create_user_access_token(user)
    
    # Create refresh token (30 days) if enabled
    refresh_token = None
    if settings.REFRESH_TOKEN_ENABLED:
        refresh_token = AuthService.create_user_refresh_token(user)

    # Update last login
    user.last_login_at = datetime.now(timezone.utc)
    db.add(user)
    db.commit()

    response = {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token,
        "expires_in": 86400,  # 1 day in seconds
        "user": UserResponse.from_orm(user)
    }
    
    # Add warning if email not verified
    if not user.email_verified:
        response["warning"] = "Please verify your email to unlock all features"
    
    return response


@router.post("/refresh")
def refresh_token(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Refresh access token using refresh token.
    
    Send your refresh_token in Authorization header.
    Returns a new access_token (valid for 1 day).
    
    Frontend should call this:
    - When access token expires (check expires_in)
    - Or automatically every 23 hours
    """
    # Decode and validate refresh token
    token_data = decode_access_token(token)
    
    # Validate it's a refresh token
    if token_data.get("token_type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid token type. Refresh token required."
        )
    
    # Check if token is blacklisted
    from app.services.token_blacklist_service import TokenBlacklistService
    if TokenBlacklistService.is_token_blacklisted(db, token_data.jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked"
        )
    
    # Get user
    user = db.query(User).filter(User.id == token_data.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    # Update last activity
    user.last_login_at = datetime.now(timezone.utc)
    db.add(user)
    db.commit()

    # Create new access token (refresh token stays the same)
    new_access_token = AuthService.create_user_access_token(user)
    
    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        "expires_in": 86400,  # 1 day
        "user": UserResponse.from_orm(user)
    }


@router.post("/logout")
def logout(
    request: Request,
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
):
    # Extract client info
    ip_address = request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or request.headers.get("X-Real-IP", "") or (request.client.host if request.client else None)
    user_agent = request.headers.get("User-Agent")
    
    token_data = decode_access_token(token)
    AuthService.logout_user(db, token_data, ip_address, user_agent)
    return {"message": "Successfully logged out"}
    

@router.post("/register")
@limiter.limit("3/minute")  # Max 3 registrations per minute
def register_customer(request: Request, registration: CustomerRegistration, db: Session = Depends(get_db)):
    """
    Register a new customer account.
    
    After registration:
    1. You can login immediately with your credentials
    2. A verification email has been sent (check logs in development)
    3. Please verify your email to unlock all features
    """
    # Extract client info
    ip_address = request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or request.headers.get("X-Real-IP", "") or (request.client.host if request.client else None)
    user_agent = request.headers.get("User-Agent")
    
    user = AuthService.register_customer(db, registration, ip_address, user_agent)
    
    return {
        "message": "Registration successful! You can now login.",
        "user": UserResponse.from_orm(user),
        "email_verified": user.email_verified,
        "next_steps": [
            "Login with your credentials at /api/login",
            "Check your email for verification link",
            "Verify your email to unlock all features"
        ],
        "note": "In development mode, check application logs for the verification link"
    }
    

@router.get("/me", response_model=UserResponse)
def get_current_user_endpoint(user: User = Depends(get_current_user)):
    return user


@router.post("/forgot-password", response_model=MessageResponse)
# @limiter.limit("3/hour")  # Max 3 password reset requests per hour
def forgot_password(request: Request, forgot_req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Request password reset - sends email with 6-digit verification code
    
    Flow:
    1. User enters email
    2. System sends 6-digit code to email
    3. User verifies code at /verify-reset-code
    4. User resets password at /reset-password with returned token
    """
    AuthService.request_password_reset(db=db, email=forgot_req.email)
    return MessageResponse(
        message="If the email exists, a verification code has been sent to your email"
    )


@router.post("/verify-reset-code", response_model=VerifyResetCodeResponse)
# @limiter.limit("5/hour")  # Max 5 verification attempts per hour
def verify_reset_code(request: Request, verify_req: VerifyResetCodeRequest, db: Session = Depends(get_db)):
    """
    Verify the 6-digit code sent to email
    
    Returns a reset_token that must be used in /reset-password endpoint
    """
    reset_token = AuthService.verify_reset_code(db, verify_req.email, verify_req.code)
    return VerifyResetCodeResponse(
        message="Code verified successfully. Use the reset_token to set new password.",
        reset_token=reset_token
    )


@router.post("/reset-password", response_model=MessageResponse)
@limiter.limit("5/hour")  # Max 5 password reset attempts per hour  
def reset_password(request: Request, reset_req: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Reset password using verified reset_token
    
    You must first verify your code at /verify-reset-code to get the reset_token
    """
    AuthService.reset_password(db, reset_req.reset_token, reset_req.new_password)
    return MessageResponse(message="Password has been reset successfully")

