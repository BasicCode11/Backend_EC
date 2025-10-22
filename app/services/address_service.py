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
    def get_for_user(db: Session, user_id: int, address_id: int) -> Optional[UserAddress]:
        stmt = select(UserAddress).where(
            (UserAddress.user_id == user_id) & (UserAddress.id == address_id)
        )
        return db.execute(stmt).scalars().first()

    @staticmethod
    def create_for_user(db: Session, user_id: int, data: AddressCreate) -> UserAddress:
        # Ensure default uniqueness per user if is_default is true
        payload = data.dict()
        if payload.get("is_default"):
            db.query(UserAddress).filter(UserAddress.user_id == user_id, UserAddress.is_default == True).update({UserAddress.is_default: False})

        address = UserAddress(user_id=user_id, **payload)
        db.add(address)
        db.commit()
        db.refresh(address)
        return address

    @staticmethod
    def update_for_user(db: Session, user_id: int, address_id: int, data: AddressUpdate) -> UserAddress:
        address = AddressService.get_for_user(db, user_id, address_id)
        if not address:
            raise ValidationError("Address not found")

        payload = data.dict(exclude_unset=True)
        if payload.get("is_default"):
            db.query(UserAddress).filter(UserAddress.user_id == user_id, UserAddress.is_default == True).update({UserAddress.is_default: False})

        for field, value in payload.items():
            setattr(address, field, value)

        db.commit()
        db.refresh(address)
        return address

    @staticmethod
    def delete_for_user(db: Session, user_id: int, address_id: int) -> None:
        address = AddressService.get_for_user(db, user_id, address_id)
        if not address:
            raise ValidationError("Address not found")
        db.delete(address)
        db.commit()


