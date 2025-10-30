from __future__ import annotations
from typing import Optional, List
from pydantic import BaseModel, field_validator, Field
from app.utils.validation import CommonValidation


# ---------------------
# TOKEN SCHEMAS
# ---------------------
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[int] = None
    sub: Optional[str] = None  # Subject (email)
    uuid: Optional[str] = None
    role_id: Optional[int] = None
    permissions: Optional[List[str]] = None
    iss: Optional[str] = None   # Issuer
    exp: Optional[int] = None   # Expiration timestamp
    jti: Optional[str] = None   # Unique identifier for the token
    iat: Optional[int] = None   # Issued at timestamp
    token_type: Optional[str] = "access"  # Token type: "access" or "refresh"
    
    def get(self, key: str, default=None):
        """Helper method to get attributes like a dict"""
        return getattr(self, key, default)



class LoginRequest(BaseModel):
    email: str
    password: str

# ---------------------
# USER SCHEMAS
# ---------------------
class UserBase(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return CommonValidation.validate_email(v)


class UserResponse(BaseModel):
    """Minimal user info returned inside login response"""
    id: int
    uuid: str
    email: str
    first_name: str
    last_name: str
    role_id: Optional[int]
    email_verified: bool

    class Config:
        from_attributes = True

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class CustomerRegistration(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str
    phone: Optional[str] = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return CommonValidation.validate_email(v)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:	
        return CommonValidation.validate_password(v)

class EmailVerificationRequest(BaseModel):
    email: str
    verification_code: str

class ForgotPasswordRequest(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return CommonValidation.validate_email(v)

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return CommonValidation.validate_password(v)

class ResendVerificationRequest(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return CommonValidation.validate_email(v)

class MessageResponse(BaseModel):
    message: str