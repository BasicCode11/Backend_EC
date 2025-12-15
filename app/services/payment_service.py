import hashlib
import base64
import hmac
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from decimal import Decimal
from sqlalchemy.orm import Session
import httpx
from app.utils.generage_hast_pay import generate_aba_payway_hash
from app.models.payment import Payment
from app.models.order import Order, PaymentStatus as OrderPaymentStatus
from app.schemas.payment import (
    PaymentCreate,
    ABAPayWayCheckoutRequest,
    ABAPayWayCheckoutResponse,
    ABAPayWayCallback
)
from app.core.config import settings
from app.core.exceptions import ValidationError, NotFoundError
from app.services.audit_log_service import AuditLogService

# Note: RSA encryption is available if needed via pycryptodome
# from Crypto.PublicKey import RSA
# from Crypto.Cipher import PKCS1_v1_5
# from Crypto.Hash import SHA256


class ABAPayWayService:
    """Service for ABA PayWay payment integration"""

    @staticmethod
    def _get_base64_encode(data: str) -> str:
        """Encode data to base64"""
        return base64.b64encode(data.encode()).decode()

    @staticmethod
    def _create_hash(data: str) -> str:
        """Create SHA256 hash with HMAC using public key"""
        return hmac.new(
            settings.ABA_PAYWAY_PUBLIC_KEY.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()

    @staticmethod
    def _get_transaction_id(order_id: int) -> str:
        """Generate unique transaction ID for order"""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        return f"ORD{order_id}-{timestamp}"

    @staticmethod
    def _format_amount(amount: Decimal) -> str:
        """Format amount to 2 decimal places as string"""
        return f"{float(amount):.2f}"

    @staticmethod
    def create_checkout_request(
        db: Session,
        order: Order,
        request_data: ABAPayWayCheckoutRequest
    ) -> ABAPayWayCheckoutResponse:
        """
        Create ABA PayWay checkout request
        
        Returns checkout URL for customer to complete payment
        """
        # Generate transaction ID
        transaction_id = ABAPayWayService._get_transaction_id(order.id)
        
        # Get current timestamp
        req_time = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        
        # Format amount (2 decimal places)
        amount = ABAPayWayService._format_amount(order.total_amount)

        
        
        # Prepare return URLs
        return_url = request_data.return_url or settings.ABA_PAYWAY_RETURN_URL
        continue_success_url = request_data.continue_url or settings.ABA_PAYWAY_CONTINUE_URL
        cancel_url = request_data.cancel_url or settings.ABA_PAYWAY_CANCEL_URL
        
        # Prepare request payload
        payload = {
            "req_time": req_time,
            "merchant_id": settings.ABA_PAYWAY_MERCHANT_ID,
            "tran_id": transaction_id,
            "amount": amount,
            "return_url": return_url,
            "continue_success_url": continue_success_url,
            "cancel_url": cancel_url,
            "payment_option": "abapay",  # Allow both cards and ABA app
            "currency": "USD",  # or "KHR" for Khmer Riel
            "items": json.dumps([{
                "name": f"Order #{order.order_number}",
                "quantity": str(order.total_items),
                "price": amount
            }]),
            "shipping": "0.00",
            "firstname": order.user.first_name if order.user else "Guest",
            "lastname": order.user.last_name if order.user else "Customer",
            "email": order.user.email if order.user else "",
            "phone": order.user.phone if order.user else "",
        }
        payload['hash'] = generate_aba_payway_hash(payload , settings.ABA_PAYWAY_PUBLIC_KEY)
        # Create payment record
        payment = Payment(
            order_id=order.id,
            payment_method="aba_payway",
            amount=order.total_amount,
            status="pending",
            payment_gateway_transaction_id=transaction_id,  # Fixed: correct field name
            gateway_response={  # Fixed: correct field name
                "req_time": req_time,
                "merchant_id": settings.ABA_PAYWAY_MERCHANT_ID,
                "return_url": return_url,
                "continue_success_url": continue_success_url,
                "cancel_url": cancel_url
            }
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)
        
        # Log payment initiation
        AuditLogService.log_create(
            db=db,
            user_id=order.user_id,
            entity_type="PAYMENT_INITIATED",
            entity_id=payment.id,
            new_values=f"ABA PayWay payment initiated for order {order.order_number}. Transaction ID: {transaction_id}"
        )
        
        # ABA PayWay uses form-based checkout, not API POST
        # Build checkout URL that frontend will redirect to
        # The URL should contain the payment parameters
        
        # Store payment details for frontend to submit
        payment.gateway_response["checkout_payload"] = payload
        db.commit()
        
        # Construct checkout URL
        # For ABA PayWay, the checkout URL is the API endpoint
        # Frontend needs to POST form data to this URL
        checkout_url = settings.ABA_PAYWAY_API_URL
        
        return ABAPayWayCheckoutResponse(
            transaction_id=transaction_id,
            checkout_url=checkout_url,
            payment_data=payload,  # Include payload for frontend
            expires_at=None  # ABA PayWay typically has 30 min expiry
        )

    @staticmethod
    def get_transaction_detail(
        db: Session,
        transaction_id: str
    ) -> Dict[str, Any]:
        """
        Call ABA PayWay API to get transaction details
        
        This is the verification step (Step 6 in the flow):
        - Called after ABA callback to verify the payment
        - Uses the check-transaction or get-transaction-details API
        """
        # Find our payment record
        payment = db.query(Payment).filter(
            Payment.payment_gateway_transaction_id == transaction_id
        ).first()
        
        if not payment:
            raise NotFoundError(f"Payment with transaction ID {transaction_id} not found")
        
        order = db.query(Order).filter(Order.id == payment.order_id).first()
        if not order:
            raise NotFoundError(f"Order with ID {payment.order_id} not found")
        
        # Prepare request for ABA check-transaction API
        req_time = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        
        # Build hash for check transaction: req_time + merchant_id + tran_id
        hash_string = f"{req_time}{settings.ABA_PAYWAY_MERCHANT_ID}{transaction_id}"
        
        print(f"=== CHECK TRANSACTION DEBUG ===")
        print(f"Transaction ID: {transaction_id}")
        print(f"Merchant ID: {settings.ABA_PAYWAY_MERCHANT_ID}")
        print(f"Req Time: {req_time}")
        print(f"Hash String: {hash_string}")
        
        check_hash = hmac.new(
            settings.ABA_PAYWAY_PUBLIC_KEY.encode('utf-8'),
            hash_string.encode('utf-8'),
            hashlib.sha512
        )
        hash_value = base64.b64encode(check_hash.digest()).decode('utf-8')
        
        print(f"Hash Value: {hash_value}")
        print(f"URL: {settings.ABA_PAYWAY_CHECK_TRANSACTION_URL}")
        
        check_data = {
            "req_time": req_time,
            "merchant_id": settings.ABA_PAYWAY_MERCHANT_ID,
            "tran_id": transaction_id,
            "hash": hash_value
        }
        
        print(f"Request Data: {check_data}")
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    settings.ABA_PAYWAY_CHECK_TRANSACTION_URL,
                    data=check_data,  # Use form data, not JSON
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                print(f"ABA Check Transaction Response: {response.status_code}")
                print(f"ABA Check Transaction Body: {response.text}")
                
                response_data = response.json()
                
                # Store check response
                if payment.gateway_response is None:
                    payment.gateway_response = {}
                payment.gateway_response["aba_check_response"] = response_data
                payment.gateway_response["checked_at"] = datetime.now(timezone.utc).isoformat()
                
                # Parse response
                status = response_data.get("status", {})
                data = response_data.get("data", {})
                
                print(f"ABA Response Status: {status}")
                print(f"ABA Response Data: {data}")
                
                if status.get("code") == "00":
                    # Successful response from ABA
                    payment_status = data.get("payment_status", "").upper()
                    
                    print(f"Payment Status from ABA: {payment_status}")
                    
                    # Check for successful payment statuses
                    # ABA may return: APPROVED, COMPLETED, SUCCESS, CAPTURED
                    if payment_status in ["APPROVED", "COMPLETED", "SUCCESS", "CAPTURED", "PAID"]:
                        # Payment verified as successful
                        payment.status = "completed"
                        payment.gateway_response["paid_at"] = datetime.now(timezone.utc).isoformat()
                        payment.gateway_response["apv"] = data.get("apv")
                        order.payment_status = OrderPaymentStatus.PAID.value
                        
                        AuditLogService.log_action(
                            db=db,
                            user_id=order.user_id,
                            action="PAYMENT_VERIFIED",
                            resource_type="Payment",
                            resource_id=payment.id,
                            details=f"Payment verified with ABA for order {order.order_number}"
                        )
                        
                        db.commit()
                        
                        return {
                            "status": "completed",
                            "verified": True,
                            "payment_status": payment_status,
                            "order_id": order.id,
                            "order_number": order.order_number,
                            "amount": data.get("total_amount"),
                            "transaction_id": transaction_id,
                            "apv": data.get("apv")
                        }
                    
                    elif payment_status in ["PENDING", "PROCESSING", "INITIATED", ""]:
                        # Still pending - don't commit changes
                        return {
                            "status": "pending",
                            "verified": True,
                            "payment_status": payment_status or "PENDING",
                            "order_id": order.id,
                            "message": "Payment is still processing"
                        }
                    
                    else:
                        # Payment failed or cancelled
                        payment.status = "failed"
                        order.payment_status = OrderPaymentStatus.FAILED.value
                        db.commit()
                        
                        return {
                            "status": "failed",
                            "verified": True,
                            "payment_status": payment_status,
                            "order_id": order.id,
                            "message": f"Payment {payment_status.lower()}"
                        }
                else:
                    # Error from ABA API
                    error_msg = status.get("message", "Unknown error")
                    print(f"ABA API Error: {error_msg}")
                    
                    return {
                        "status": "error",
                        "verified": False,
                        "order_id": order.id,
                        "message": error_msg
                    }
                    
        except httpx.RequestError as e:
            print(f"ABA Check Transaction Error: {str(e)}")
            return {
                "status": "error",
                "verified": False,
                "order_id": order.id if order else None,
                "message": f"Failed to verify with ABA: {str(e)}"
            }


    @staticmethod
    def verify_callback(
        db: Session,
        callback_data: ABAPayWayCallback
    ) -> Dict[str, Any]:
        """
        Verify ABA PayWay payment callback
        
        This is called when ABA redirects back to your app
        """
        # Verify hash
        hash_string = (
            f"{callback_data.tran_id}"
            f"{callback_data.req_time}"
            f"{callback_data.amount}"
            f"{callback_data.merchant_id}"
        )
        
        expected_hash = ABAPayWayService._create_hash(hash_string)
        
        if callback_data.hash != expected_hash:
            raise ValidationError("Invalid payment callback hash")
        
        # Find payment by transaction ID
        payment = db.query(Payment).filter(
            Payment.payment_gateway_transaction_id == callback_data.tran_id
        ).first()
        
        if not payment:
            raise NotFoundError(f"Payment with transaction ID {callback_data.tran_id} not found")
        
        # Get order
        order = db.query(Order).filter(Order.id == payment.order_id).first()
        
        if not order:
            raise NotFoundError(f"Order with ID {payment.order_id} not found")
        
        # Check status
        # ABA PayWay callback includes status: 0 = success, 1 = failed
        payment_status = callback_data.status
        
        if payment_status == "0" or callback_data.payment_option:
            # Payment successful
            payment.status = "completed"
            # Note: Payment model doesn't have paid_at field, using updated_at
            if payment.gateway_response is None:
                payment.gateway_response = {}
            payment.gateway_response["callback_data"] = callback_data.dict()
            payment.gateway_response["verified_at"] = datetime.now(timezone.utc).isoformat()
            payment.gateway_response["paid_at"] = datetime.now(timezone.utc).isoformat()
            
            # Update order payment status
            order.payment_status = OrderPaymentStatus.PAID.value
            
            # Log success
            AuditLogService.log_action(
                db=db,
                user_id=order.user_id,
                action="PAYMENT_COMPLETED",
                resource_type="Payment",
                resource_id=payment.id,
                details=f"ABA PayWay payment completed for order {order.order_number}. Amount: {callback_data.amount}"
            )
            
        else:
            # Payment failed
            payment.status = "failed"
            if payment.gateway_response is None:
                payment.gateway_response = {}
            payment.gateway_response["callback_data"] = callback_data.dict()
            payment.gateway_response["failed_at"] = datetime.now(timezone.utc).isoformat()
            
            # Update order payment status
            order.payment_status = OrderPaymentStatus.FAILED.value
            
            # Log failure
            AuditLogService.log_action(
                db=db,
                user_id=order.user_id,
                action="PAYMENT_FAILED",
                resource_type="Payment",
                resource_id=payment.id,
                details=f"ABA PayWay payment failed for order {order.order_number}"
            )
        
        db.commit()
        db.refresh(payment)
        db.refresh(order)
        
        return {
            "payment_id": payment.id,
            "order_id": order.id,
            "order_number": order.order_number,
            "status": payment.status,
            "amount": float(payment.amount),
            "transaction_id": payment.payment_gateway_transaction_id
        }

    @staticmethod
    def check_payment_status(
        db: Session,
        transaction_id: str
    ) -> Dict[str, Any]:
        """Check payment status by transaction ID"""
        payment = db.query(Payment).filter(
            Payment.payment_gateway_transaction_id == transaction_id
        ).first()
        
        if not payment:
            raise NotFoundError(f"Payment with transaction ID {transaction_id} not found")
        
        order = db.query(Order).filter(Order.id == payment.order_id).first()
        
        # Get paid_at from gateway_response if available
        paid_at = None
        if payment.gateway_response and "paid_at" in payment.gateway_response:
            paid_at = payment.gateway_response["paid_at"]
        
        return {
            "payment_id": payment.id,
            "order_id": order.id,
            "order_number": order.order_number,
            "status": payment.status,
            "amount": float(payment.amount),
            "transaction_id": payment.payment_gateway_transaction_id,
            "paid_at": paid_at,
            "created_at": payment.created_at.isoformat()
        }


class PaymentService:
    """General payment service"""

    @staticmethod
    def create_payment(
        db: Session,
        payment_data: PaymentCreate,
        user_id: Optional[int] = None
    ) -> Payment:
        """Create payment record"""
        # Verify order exists
        order = db.query(Order).filter(Order.id == payment_data.order_id).first()
        if not order:
            raise NotFoundError(f"Order with ID {payment_data.order_id} not found")
        
        # Create payment
        payment = Payment(
            order_id=payment_data.order_id,
            payment_method=payment_data.payment_method.value,
            amount=payment_data.amount,
            status="pending",
            payment_gateway_transaction_id=payment_data.transaction_id,
            gateway_response=payment_data.payment_details or {}
        )
        
        db.add(payment)
        db.commit()
        db.refresh(payment)
        
        return payment

    @staticmethod
    def get_payment_by_order(db: Session, order_id: int) -> Optional[Payment]:
        """Get payment by order ID"""
        return db.query(Payment).filter(
            Payment.order_id == order_id
        ).order_by(Payment.created_at.desc()).first()

    @staticmethod
    def get_payment_by_transaction(db: Session, transaction_id: str) -> Optional[Payment]:
        """Get payment by transaction ID"""
        return db.query(Payment).filter(
            Payment.payment_gateway_transaction_id == transaction_id
        ).first()
