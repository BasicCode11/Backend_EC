from typing import List, Optional, Tuple
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session, selectinload
from math import ceil

from app.models.review import Review
from app.models.user import User
from app.models.product import Product
from app.models.order import Order
from app.models.order_item import OrderItem
from app.schemas.review import ReviewCreate, ReviewUpdate, ReviewApprovalUpdate
from app.core.exceptions import ValidationError, NotFoundError, ForbiddenException


class ReviewService:
    """Service for managing product reviews"""

    @staticmethod
    def create_review(
        db: Session,
        user_id: int,
        review_data: ReviewCreate
    ) -> Review:
        """Create a new review"""
        # Check if product exists
        product = db.query(Product).filter(Product.id == review_data.product_id).first()
        if not product:
            raise NotFoundError(f"Product with ID {review_data.product_id} not found")
        
        # Check if user already reviewed this product
        existing_review = db.query(Review).filter(
            and_(
                Review.product_id == review_data.product_id,
                Review.user_id == user_id
            )
        ).first()
        
        if existing_review:
            raise ValidationError("You have already reviewed this product")
        
        # Check if this is a verified purchase
        # User must have ordered and received this product
        order_id = None
        verified_purchase = db.query(OrderItem).join(Order).filter(
            and_(
                OrderItem.product_id == review_data.product_id,
                Order.user_id == user_id,
                Order.status.in_(["delivered", "completed"])
            )
        ).first()
        
        if verified_purchase:
            order_id = verified_purchase.order_id
        
        # Create review
        review = Review(
            product_id=review_data.product_id,
            user_id=user_id,
            order_id=order_id,
            rating=review_data.rating,
            title=review_data.title,
            comment=review_data.comment,
            is_approved=False  # Requires admin approval
        )
        
        db.add(review)
        db.commit()
        db.refresh(review)
        
        return review

    @staticmethod
    def get_product_reviews(
        db: Session,
        product_id: int,
        page: int = 1,
        limit: int = 20,
        approved_only: bool = True
    ) -> Tuple[List[Review], int, float]:
        """
        Get all reviews for a product
        Returns: (reviews, total_count, average_rating)
        """
        # Base query
        query = db.query(Review).filter(Review.product_id == product_id)
        
        if approved_only:
            query = query.filter(Review.is_approved == True)
        
        # Get total count
        total = query.count()
        
        # Calculate average rating
        avg_rating = db.query(func.avg(Review.rating)).filter(
            Review.product_id == product_id,
            Review.is_approved == True
        ).scalar()
        
        # Get paginated reviews
        skip = (page - 1) * limit
        reviews = query.options(
            selectinload(Review.user)
        ).order_by(
            Review.created_at.desc()
        ).offset(skip).limit(limit).all()
        
        return reviews, total, float(avg_rating) if avg_rating else 0.0

    @staticmethod
    def get_user_reviews(
        db: Session,
        user_id: int,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[Review], int]:
        """Get all reviews by a user"""
        query = db.query(Review).filter(Review.user_id == user_id)
        
        total = query.count()
        skip = (page - 1) * limit
        
        reviews = query.options(
            selectinload(Review.product)
        ).order_by(
            Review.created_at.desc()
        ).offset(skip).limit(limit).all()
        
        return reviews, total

    @staticmethod
    def get_review_by_id(db: Session, review_id: int) -> Review:
        """Get a review by ID"""
        review = db.query(Review).options(
            selectinload(Review.user),
            selectinload(Review.product)
        ).filter(Review.id == review_id).first()
        
        if not review:
            raise NotFoundError(f"Review with ID {review_id} not found")
        
        return review

    @staticmethod
    def update_review(
        db: Session,
        review_id: int,
        user_id: int,
        update_data: ReviewUpdate
    ) -> Review:
        """Update a review (only by owner)"""
        review = ReviewService.get_review_by_id(db, review_id)
        
        # Check if user owns this review
        if review.user_id != user_id:
            raise ForbiddenException("You can only update your own reviews")
        
        # Update fields
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(review, key, value)
        
        # Reset approval if content changed
        if 'rating' in update_dict or 'title' in update_dict or 'comment' in update_dict:
            review.is_approved = False
        
        db.commit()
        db.refresh(review)
        
        return review

    @staticmethod
    def delete_review(
        db: Session,
        review_id: int,
        user_id: int,
        is_admin: bool = False
    ) -> None:
        """Delete a review (owner or admin)"""
        review = ReviewService.get_review_by_id(db, review_id)
        
        # Check permissions
        if not is_admin and review.user_id != user_id:
            raise ForbiddenException("You can only delete your own reviews")
        
        db.delete(review)
        db.commit()

    @staticmethod
    def approve_review(
        db: Session,
        review_id: int,
        approval_data: ReviewApprovalUpdate
    ) -> Review:
        """Approve or reject a review (admin only)"""
        review = ReviewService.get_review_by_id(db, review_id)
        
        review.is_approved = approval_data.is_approved
        
        db.commit()
        db.refresh(review)
        
        return review

    @staticmethod
    def mark_helpful(
        db: Session,
        review_id: int
    ) -> Review:
        """Mark a review as helpful"""
        review = ReviewService.get_review_by_id(db, review_id)
        
        review.increment_helpful_count()
        
        db.commit()
        db.refresh(review)
        
        return review

    @staticmethod
    def get_pending_reviews(
        db: Session,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[Review], int]:
        """Get all pending reviews (admin only)"""
        query = db.query(Review).filter(Review.is_approved == False)
        
        total = query.count()
        skip = (page - 1) * limit
        
        reviews = query.options(
            selectinload(Review.user),
            selectinload(Review.product)
        ).order_by(
            Review.created_at.desc()
        ).offset(skip).limit(limit).all()
        
        return reviews, total

    @staticmethod
    def get_product_rating_stats(db: Session, product_id: int) -> dict:
        """Get rating statistics for a product"""
        # Get all approved reviews
        reviews = db.query(Review).filter(
            Review.product_id == product_id,
            Review.is_approved == True
        ).all()
        
        if not reviews:
            return {
                "total_reviews": 0,
                "average_rating": 0.0,
                "rating_distribution": {
                    "5": 0, "4": 0, "3": 0, "2": 0, "1": 0
                }
            }
        
        # Calculate statistics
        total = len(reviews)
        avg_rating = sum(r.rating for r in reviews) / total
        
        # Rating distribution
        distribution = {"5": 0, "4": 0, "3": 0, "2": 0, "1": 0}
        for review in reviews:
            distribution[str(review.rating)] += 1
        
        return {
            "total_reviews": total,
            "average_rating": round(avg_rating, 2),
            "rating_distribution": distribution,
            "verified_purchase_count": sum(1 for r in reviews if r.is_verified_purchase)
        }
