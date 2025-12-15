from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.models.order import Order
from app.schemas.payment import (
    ABAPayWayCheckoutRequest,
    ABAPayWayCheckoutResponse,
    ABAPayWayCallback,
    PaymentVerifyRequest,
    PaymentResponse
)
from app.services.payment_service import ABAPayWayService, PaymentService
from app.services.order_service import OrderService
from app.deps.auth import get_current_active_user
from app.core.exceptions import ValidationError, NotFoundError

router = APIRouter()


@router.post("/payments/aba-payway/checkout", response_model=ABAPayWayCheckoutResponse)
def create_aba_payway_checkout(
    request: Request,
    checkout_data: ABAPayWayCheckoutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    **Create ABA PayWay checkout session**
    
    This endpoint:
    1. Validates the order exists and belongs to user
    2. Creates payment record
    3. Generates ABA PayWay checkout URL
    4. Returns checkout URL for customer to complete payment
    
    **Usage:**
    1. User places order (POST /checkout)
    2. Call this endpoint with order_id
    3. Redirect user to returned checkout_url
    4. User completes payment on ABA PayWay
    5. ABA redirects back to your return_url with payment status
    
    **Flow:**
    ```
    Your App → ABA PayWay API → Returns checkout URL
         ↓
    Redirect User → ABA PayWay Page → User Pays
         ↓
    ABA Redirects → Your return_url with payment result
    ```
    """
    try:
        # Get order
        order = OrderService.get_by_id(db, checkout_data.order_id)
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order with ID {checkout_data.order_id} not found"
            )
        
        # Verify order belongs to current user
        if order.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only pay for your own orders"
            )
        
        # Check if order is already paid
        if order.payment_status == "paid":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order is already paid"
            )
        
        # Create ABA PayWay checkout
        checkout_response = ABAPayWayService.create_checkout_request(
            db=db,
            order=order,
            request_data=checkout_data
        )
        
        return checkout_response
        
    except (ValidationError, NotFoundError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Payment initialization failed: {str(e)}"
        )


@router.post("/payments/aba-payway/callback")
def aba_payway_callback(
    request: Request,
    response: Response,
    callback_data: ABAPayWayCallback,
    db: Session = Depends(get_db)
):
    """
    **ABA PayWay payment callback endpoint**
    
    This endpoint receives payment confirmation from ABA PayWay.
    
    **BEST PRACTICE FLOW:**
    1. ABA calls this endpoint after customer pays
    2. We verify by calling ABA's get-transaction-detail API
    3. Mark order as PAID or FAILED based on verification
    4. Return success to ABA
    
    **Note:** This endpoint should be publicly accessible (no authentication)
    as it's called by ABA PayWay servers, not your frontend.
    """
    try:
        print(f"=== ABA CALLBACK RECEIVED ===")
        print(f"Transaction ID: {callback_data.tran_id}")
        print(f"Status: {callback_data.status}")
        print(f"Amount: {callback_data.amount}")
        
        # Step 1: First verify the callback itself
        result = ABAPayWayService.verify_callback(db, callback_data)
        
        # Step 2: Call ABA's API to verify the transaction (Best Practice Step 6)
        verification = ABAPayWayService.get_transaction_detail(
            db=db,
            transaction_id=callback_data.tran_id
        )
        
        print(f"ABA Verification Result: {verification}")
        
        # Return success response to ABA
        return {
            "status": "success",
            "message": "Payment callback processed and verified",
            "data": {
                "callback_result": result,
                "verification": verification
            }
        }
        
    except (ValidationError, NotFoundError) as e:
        print(f"Callback Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Log error but return 200 to prevent ABA from retrying
        print(f"Callback Exception: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }


@router.post("/payments/check-transaction")
def check_transaction_with_aba(
    verify_data: PaymentVerifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    **Check Transaction Status with ABA PayWay API**
    
    This is the MANDATORY Check Transaction API that verifies payment status 
    directly with ABA's servers.
    
    **When to use:**
    1️⃣ After callback to confirm payment status is successful
    2️⃣ If callback doesn't push to your side (network issues, etc.)
    3️⃣ Poll every 3-5 seconds after user initiates payment
    
    **Recommended polling strategy:**
    - Start polling 20 seconds after payment initiation
    - Poll every 3-5 seconds
    - Stop after 3-5 minutes (QR expires)
    - If payment is completed/successful, stop polling
    
    **Response status values:**
    - "completed": Payment successful ✅
    - "pending": Still waiting for payment ⏳
    - "failed": Payment failed or cancelled ❌
    - "error": Could not verify with ABA ⚠️
    """
    try:
        # Verify order belongs to user
        order = OrderService.get_by_id(db, verify_data.order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        if order.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unauthorized"
            )
        
        # Call ABA's Check Transaction API
        result = ABAPayWayService.get_transaction_detail(
            db=db,
            transaction_id=verify_data.transaction_id
        )
        
        print(f"Check Transaction Result: {result}")
        
        return result
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        print(f"Check Transaction Error: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }


@router.get("/payments/aba-payway/return")
def aba_payway_return(
    request: Request,
    tran_id: str,
    req_time: str,
    merchant_id: str,
    amount: str,
    hash: str,
    status: Optional[str] = None,
    payment_option: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    **ABA PayWay return URL endpoint (User-facing)**
    
    This is where ABA redirects the user after payment.
    
    **Query Parameters:**
    - tran_id: Transaction ID
    - req_time: Request timestamp
    - merchant_id: Your merchant ID
    - amount: Payment amount
    - hash: Security hash
    - status: Payment status (0=success, 1=failed)
    - payment_option: Payment method used
    
    **Usage:**
    Set this URL as your `return_url` when creating checkout.
    After payment, ABA redirects user here with payment result.
    
    **Frontend Integration:**
    ```javascript
    // In your frontend callback page
    const urlParams = new URLSearchParams(window.location.search);
    const status = urlParams.get('status');
    
    if (status === '0') {
      // Payment successful - show success page
      showSuccessMessage();
    } else {
      // Payment failed - show error
      showErrorMessage();
    }
    ```
    """
    try:
        # Create callback data from query params
        callback_data = ABAPayWayCallback(
            tran_id=tran_id,
            req_time=req_time,
            merchant_id=merchant_id,
            amount=amount,
            hash=hash,
            status=status,
            payment_option=payment_option
        )
        
        # Verify and process callback
        result = ABAPayWayService.verify_callback(db, callback_data)
        
        # Return HTML response for user
        if result["status"] == "completed":
            return {
                "status": "success",
                "message": "Payment completed successfully",
                "order_id": result["order_id"],
                "order_number": result["order_number"],
                "amount": result["amount"]
            }
        else:
            return {
                "status": "failed",
                "message": "Payment failed",
                "order_id": result["order_id"]
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@router.post("/payments/verify", response_model=dict)
def verify_payment(
    verify_data: PaymentVerifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    **Verify payment status**
    
    Check the current status of a payment by transaction ID.
    
    **Usage:**
    After user returns from ABA PayWay, call this to confirm payment status.
    """
    try:
        result = ABAPayWayService.check_payment_status(
            db=db,
            transaction_id=verify_data.transaction_id
        )
        
        # Verify order belongs to user
        order = OrderService.get_by_id(db, result["order_id"])
        if order.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unauthorized"
            )
        
        return result
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/payments/order/{order_id}", response_model=PaymentResponse)
def get_order_payment(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    **Get payment details for an order**
    
    Returns the payment record associated with an order.
    """
    # Verify order belongs to user
    order = OrderService.get_by_id(db, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    if order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized"
        )
    
    # Get payment
    payment = PaymentService.get_payment_by_order(db, order_id)
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No payment found for this order"
        )
    
    return payment
