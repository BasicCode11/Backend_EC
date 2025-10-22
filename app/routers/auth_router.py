from fastapi import APIRouter, Depends , HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta , datetime , timezone
from sqlalchemy.orm import Session
import uuid
from app.database import get_db
from app.models.user import User
from app.models.role import Role
from app.services.auth_service import AuthService
from app.schemas.auth import LoginRequest , LoginResponse , UserResponse, CustomerRegistration
from app.core.config import settings
from app.core.security import create_access_token , oauth2_scheme , decode_access_token , get_token_data, hash_password


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
    



    
