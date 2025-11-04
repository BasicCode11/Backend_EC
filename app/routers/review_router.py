from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from math import ceil

from app.database import get_db
from app.models.user import User
from app.schemas.review import (
    ReviewCreate,
    ReviewUpdate,
    ReviewApprovalUpdate,
    ReviewResponse,
    ReviewListResponse
)
from app.services.review_service import ReviewService
from app.deps.auth import get_current_active_user, require_permission
from app.core.exceptions import ValidationError, NotFoundError, ForbiddenException

router = APIRouter()


@router.post("/products/{product_id}/reviews", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def create_review(
    product_id: int,
    review_data: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    **Create a product review**
    
    - Customers can review products they purchased
    - Rating: 1-5 stars
    - Optional title and comment
    - Automatically marked as verified purchase if ordered
    - Requires admin approval before showing publicly
    
    **Restrictions:**
    - Can only review once per product
    - Must be authenticated
    """
    try:
        # Override product_id from URL
        review_data.product_id = product_id
        
        review = ReviewService.create_review(
            db=db,
            user_id=current_user.id,
            review_data=review_data
        )
        
        # Build response
        return ReviewResponse(
            id=review.id,
            product_id=review.product_id,
            user_id=review.user_id,
            order_id=review.order_id,
            rating=review.rating,
            title=review.title,
            comment=review.comment,
            is_approved=review.is_approved,
            helpful_count=review.helpful_count,
            is_verified_purchase=review.is_verified_purchase,
            user_name=f"{review.user.first_name} {review.user.last_name}" if review.user else None,
            created_at=review.created_at,
            updated_at=review.updated_at
        )
    
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/products/{product_id}/reviews", response_model=ReviewListResponse)
def get_product_reviews(
    product_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    **Get all approved reviews for a product**
    
    Returns:
    - List of reviews with user names
    - Total count
    - Average rating
    - Pagination info
    
    **Filters:**
    - Only approved reviews shown
    - Sorted by newest first
    """
    reviews, total, avg_rating = ReviewService.get_product_reviews(
        db=db,
        product_id=product_id,
        page=page,
        limit=limit,
        approved_only=True
    )
    
    pages = ceil(total / limit) if total > 0 else 1
    
    # Build response items
    items = []
    for review in reviews:
        user_name = f"{review.user.first_name} {review.user.last_name}" if review.user else "Anonymous"
        items.append(ReviewResponse(
            id=review.id,
            product_id=review.product_id,
            user_id=review.user_id,
            order_id=review.order_id,
            rating=review.rating,
            title=review.title,
            comment=review.comment,
            is_approved=review.is_approved,
            helpful_count=review.helpful_count,
            is_verified_purchase=review.is_verified_purchase,
            user_name=user_name,
            created_at=review.created_at,
            updated_at=review.updated_at
        ))
    
    return ReviewListResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        pages=pages,
        average_rating=avg_rating
    )


@router.get("/products/{product_id}/reviews/stats")
def get_product_rating_stats(
    product_id: int,
    db: Session = Depends(get_db)
):
    """
    **Get rating statistics for a product**
    
    Returns:
    - Total reviews count
    - Average rating
    - Rating distribution (1-5 stars)
    - Verified purchase count
    
    Useful for displaying rating summary on product pages
    """
    stats = ReviewService.get_product_rating_stats(db, product_id)
    return stats


@router.get("/reviews/me", response_model=ReviewListResponse)
def get_my_reviews(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    **Get all my reviews**
    
    Returns all reviews written by the current user,
    including both approved and pending reviews.
    """
    reviews, total = ReviewService.get_user_reviews(
        db=db,
        user_id=current_user.id,
        page=page,
        limit=limit
    )
    
    pages = ceil(total / limit) if total > 0 else 1
    
    items = []
    for review in reviews:
        items.append(ReviewResponse(
            id=review.id,
            product_id=review.product_id,
            user_id=review.user_id,
            order_id=review.order_id,
            rating=review.rating,
            title=review.title,
            comment=review.comment,
            is_approved=review.is_approved,
            helpful_count=review.helpful_count,
            is_verified_purchase=review.is_verified_purchase,
            user_name=f"{current_user.first_name} {current_user.last_name}",
            created_at=review.created_at,
            updated_at=review.updated_at
        ))
    
    return ReviewListResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        pages=pages,
        average_rating=None
    )


@router.get("/reviews/{review_id}", response_model=ReviewResponse)
def get_review(
    review_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific review by ID"""
    try:
        review = ReviewService.get_review_by_id(db, review_id)
        
        user_name = f"{review.user.first_name} {review.user.last_name}" if review.user else "Anonymous"
        
        return ReviewResponse(
            id=review.id,
            product_id=review.product_id,
            user_id=review.user_id,
            order_id=review.order_id,
            rating=review.rating,
            title=review.title,
            comment=review.comment,
            is_approved=review.is_approved,
            helpful_count=review.helpful_count,
            is_verified_purchase=review.is_verified_purchase,
            user_name=user_name,
            created_at=review.created_at,
            updated_at=review.updated_at
        )
    
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.put("/reviews/{review_id}", response_model=ReviewResponse)
def update_review(
    review_id: int,
    update_data: ReviewUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    **Update your own review**
    
    - Can only update your own reviews
    - Updating requires re-approval by admin
    - Can update rating, title, or comment
    """
    try:
        review = ReviewService.update_review(
            db=db,
            review_id=review_id,
            user_id=current_user.id,
            update_data=update_data
        )
        
        return ReviewResponse(
            id=review.id,
            product_id=review.product_id,
            user_id=review.user_id,
            order_id=review.order_id,
            rating=review.rating,
            title=review.title,
            comment=review.comment,
            is_approved=review.is_approved,
            helpful_count=review.helpful_count,
            is_verified_purchase=review.is_verified_purchase,
            user_name=f"{current_user.first_name} {current_user.last_name}",
            created_at=review.created_at,
            updated_at=review.updated_at
        )
    
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ForbiddenException as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.delete("/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    **Delete your own review**
    
    Only the review owner can delete their review.
    Admins can delete any review.
    """
    try:
        # Check if user is admin
        is_admin = any(role.name == "admin" for role in current_user.roles)
        
        ReviewService.delete_review(
            db=db,
            review_id=review_id,
            user_id=current_user.id,
            is_admin=is_admin
        )
        
        return None
    
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ForbiddenException as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.post("/reviews/{review_id}/helpful", response_model=ReviewResponse)
def mark_review_helpful(
    review_id: int,
    db: Session = Depends(get_db)
):
    """
    **Mark a review as helpful**
    
    Increments the helpful count for the review.
    No authentication required.
    """
    try:
        review = ReviewService.mark_helpful(db, review_id)
        
        user_name = f"{review.user.first_name} {review.user.last_name}" if review.user else "Anonymous"
        
        return ReviewResponse(
            id=review.id,
            product_id=review.product_id,
            user_id=review.user_id,
            order_id=review.order_id,
            rating=review.rating,
            title=review.title,
            comment=review.comment,
            is_approved=review.is_approved,
            helpful_count=review.helpful_count,
            is_verified_purchase=review.is_verified_purchase,
            user_name=user_name,
            created_at=review.created_at,
            updated_at=review.updated_at
        )
    
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# Admin endpoints
@router.get("/admin/reviews/pending", response_model=ReviewListResponse)
def get_pending_reviews(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["reviews:manage"]))
):
    """
    **Get all pending reviews (Admin only)**
    
    Returns reviews awaiting approval.
    Requires `reviews:manage` permission.
    """
    reviews, total = ReviewService.get_pending_reviews(
        db=db,
        page=page,
        limit=limit
    )
    
    pages = ceil(total / limit) if total > 0 else 1
    
    items = []
    for review in reviews:
        user_name = f"{review.user.first_name} {review.user.last_name}" if review.user else "Anonymous"
        items.append(ReviewResponse(
            id=review.id,
            product_id=review.product_id,
            user_id=review.user_id,
            order_id=review.order_id,
            rating=review.rating,
            title=review.title,
            comment=review.comment,
            is_approved=review.is_approved,
            helpful_count=review.helpful_count,
            is_verified_purchase=review.is_verified_purchase,
            user_name=user_name,
            created_at=review.created_at,
            updated_at=review.updated_at
        ))
    
    return ReviewListResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        pages=pages,
        average_rating=None
    )


@router.post("/admin/reviews/{review_id}/approve", response_model=ReviewResponse)
def approve_review(
    review_id: int,
    approval_data: ReviewApprovalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["reviews:manage"]))
):
    """
    **Approve or reject a review (Admin only)**
    
    Set is_approved to true to approve, false to reject.
    Requires `reviews:manage` permission.
    """
    try:
        review = ReviewService.approve_review(
            db=db,
            review_id=review_id,
            approval_data=approval_data
        )
        
        user_name = f"{review.user.first_name} {review.user.last_name}" if review.user else "Anonymous"
        
        return ReviewResponse(
            id=review.id,
            product_id=review.product_id,
            user_id=review.user_id,
            order_id=review.order_id,
            rating=review.rating,
            title=review.title,
            comment=review.comment,
            is_approved=review.is_approved,
            helpful_count=review.helpful_count,
            is_verified_purchase=review.is_verified_purchase,
            user_name=user_name,
            created_at=review.created_at,
            updated_at=review.updated_at
        )
    
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
