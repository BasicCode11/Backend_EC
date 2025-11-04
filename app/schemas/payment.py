from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal
from enum import Enum


class PaymentMethod(str, Enum):
    ABA_PAYWAY = "aba_payway"
    CASH_ON_DELIVERY = "cash_on_delivery"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


# ABA PayWay Request
class ABAPayWayCheckoutRequest(BaseModel):
    """Request to initiate ABA PayWay checkout"""
    order_id: int
    return_url: Optional[str] = None
    continue_url: Optional[str] = None
    cancel_url: Optional[str] = None


class ABAPayWayCheckoutResponse(BaseModel):
    """Response from ABA PayWay checkout initiation"""
    transaction_id: str
    checkout_url: str
    payment_data: Optional[dict] = None  # Form data for frontend to POST
    qr_code: Optional[str] = None
    expires_at: Optional[datetime] = None


# Payment Callback/Webhook
class ABAPayWayCallback(BaseModel):
    """ABA PayWay payment callback data"""
    tran_id: str
    req_time: str
    merchant_id: str
    amount: str
    hash: str
    status: Optional[str] = None
    payment_option: Optional[str] = None


# Payment Record
class PaymentCreate(BaseModel):
    order_id: int
    payment_method: PaymentMethod
    amount: Decimal
    transaction_id: Optional[str] = None
    payment_details: Optional[dict] = None


class PaymentResponse(BaseModel):
    id: int
    order_id: int
    payment_method: str
    amount: Decimal
    status: str
    transaction_id: Optional[str] = None
    payment_details: Optional[dict] = None
    paid_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaymentVerifyRequest(BaseModel):
    """Request to verify payment status"""
    transaction_id: str
    order_id: int
