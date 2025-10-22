from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class AddressBase(BaseModel):
    address_type: str = Field(default="home")
    label: Optional[str] = None
    recipient_name: Optional[str] = None
    company: Optional[str] = None
    street_address: str
    apartment_suite: Optional[str] = None
    city: str
    state: str
    country: str = Field(default="US")
    postal_code: str
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    is_default: Optional[bool] = False
    is_active: Optional[bool] = True


class AddressCreate(AddressBase):
    pass


class AddressUpdate(BaseModel):
    address_type: Optional[str] = None
    label: Optional[str] = None
    recipient_name: Optional[str] = None
    company: Optional[str] = None
    street_address: Optional[str] = None
    apartment_suite: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None


class AddressResponse(AddressBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


