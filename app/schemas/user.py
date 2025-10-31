from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from app.schemas.address import AddressResponse , AddressCreate

class UserBase(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str
    role_id: int
    phone: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role_id: Optional[int] = None
    phone: Optional[str] = None
    email_verified: Optional[bool] = None

class UserSelfUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    picture: Optional[str] = None
    comfime_password: Optional[str] = None
    password: Optional[str] = None

class RoleOut(BaseModel):
    id: int
    name:str


class UserResponse(BaseModel):
    id: int
    uuid: str
    email: str
    first_name: str
    last_name: str
    role: RoleOut
    phone: Optional[str] = None
    picture: Optional[str] = None
    email_verified: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserWithRelations(UserResponse):
    role: Optional[dict] = None


#for create both in one short
class UserProfileBundle(BaseModel):
    user: UserResponse
    addresses: List[AddressResponse] = []

class UserWithAddressCreate(BaseModel):
    user: UserCreate
    address: AddressCreate

class UserSearchParams(BaseModel):
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role_id: Optional[int] = None
    email_verified: Optional[bool] = None
    skip: int = 0
    limit: int = 100


class UserWithPerPage(BaseModel):
    item: list[UserProfileBundle]
    total: int
    page: int
    limit: int
    class Config:
        from_attributes = True