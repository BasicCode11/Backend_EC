from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.user_address import UserAddress
from app.models.user import User
from app.schemas.address import AddressCreate, AddressUpdate
from app.core.exceptions import ValidationError, ForbiddenException


class AddressService:
    @staticmethod
    def list_for_user(db: Session, user_id: int) -> List[UserAddress]:
        stmt = select(UserAddress).where(UserAddress.user_id == user_id)
        return db.execute(stmt).scalars().all()

    @staticmethod
    def get_for_user(db: Session, user_id: int) -> Optional[UserAddress]:
        stmt = select(UserAddress).where(
            UserAddress.user_id == user_id
        )
        return db.execute(stmt).scalars().first()

    @staticmethod
    def create_for_user(db: Session, user: User, data: AddressCreate) -> UserAddress:
        """Create address for a user. Accepts User object or user_id (int)"""
        user_id = user.id if isinstance(user, User) else user
        if not user_id:
            raise ValidationError("User not found")
        if AddressService.list_for_user(db, user_id):
            raise ValidationError("User already has an address")
        
        payload = data.model_dump()
        if payload.get("is_default"):
            db.query(UserAddress).filter(
                UserAddress.user_id == user_id, 
                UserAddress.is_default == True
            ).update({UserAddress.is_default: False})
            db.flush()

        address = UserAddress(user_id=user_id, **payload)
        db.add(address)
        db.commit()
        db.refresh(address)
        return address

    @staticmethod
    def update_for_user(db: Session, user_id: int, data: AddressUpdate) -> UserAddress:
        """Update address for a user. If address_id is None, update by user_id (for single address)"""
        
        address = AddressService.get_for_user(db, user_id)
        if not address:
            raise ValidationError("Address not found")

        payload = data.model_dump(exclude_unset=True)
        if payload.get("is_default"):
            db.query(UserAddress).filter(
                UserAddress.user_id == user_id, 
                UserAddress.is_default == True,
                UserAddress.id != address.id
            ).update({UserAddress.is_default: False})
            db.flush()

        for field, value in payload.items():
            setattr(address, field, value)

        db.commit()
        db.refresh(address)
        return address

    @staticmethod
    def delete_for_user(db: Session, user_id: int, address_id: int) -> None:
        address = db.query(UserAddress).filter(
            UserAddress.user_id == user_id,
            UserAddress.id == address_id
        ).first()
        if not address:
            raise ValidationError("Address not found")
        db.delete(address)
        db.commit()


