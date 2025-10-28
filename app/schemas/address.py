from typing import Optional
from pydantic import BaseModel, Field, field_validator
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
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Longitude must be between -180 and 180")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Latitude must be between -90 and 90")
    is_default: Optional[bool] = False
    is_active: Optional[bool] = True

    @field_validator('longitude')
    @classmethod
    def validate_longitude(cls, v):
        if v is not None and (v < -180 or v > 180):
            raise ValueError('Longitude must be between -180 and 180')
        return v

    @field_validator('latitude')
    @classmethod
    def validate_latitude(cls, v):
        if v is not None and (v < -90 or v > 90):
            raise ValueError('Latitude must be between -90 and 90')
        return v


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


