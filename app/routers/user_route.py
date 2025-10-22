from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.models.user import User
from app.database import get_db
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserWithRelations,
    UserSearchParams,
    UserSelfUpdate,
    UserProfileBundle,
)
from app.schemas.address import AddressCreate, AddressUpdate, AddressResponse
from app.services.address_service import AddressService
from app.services.user_service import UserService
from app.deps.auth import (
    get_current_user,
    get_current_active_user,
    require_super_admin,
    require_permission,
)

router = APIRouter()

@router.get("/me/profile", response_model=UserProfileBundle)
def read_my_profile_bundle(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    addresses = AddressService.list_for_user(db, current_user.id)
    return {"user": current_user, "addresses": addresses}


# Customer self-service address endpoints
@router.get("/me/addresses", response_model=List[AddressResponse])
def list_my_addresses(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return AddressService.list_for_user(db, current_user.id)


@router.post("/me/addresses", response_model=AddressResponse)
def create_my_address(
    data: AddressCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return AddressService.create_for_user(db, current_user.id, data)


@router.put("/me/addresses/{address_id}", response_model=AddressResponse)
def update_my_address(
    address_id: int,
    data: AddressUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return AddressService.update_for_user(db, current_user.id, address_id, data)


@router.delete("/me/addresses/{address_id}")
def delete_my_address(
    address_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    AddressService.delete_for_user(db, current_user.id, address_id)
    return {"message": "Address deleted"}


@router.get("/user", response_model=List[UserWithRelations])
def read_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    role_id: Optional[int] = None,
    email_verified: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["users:read"])),
):
    """List users with optional filters - Admin only"""
    return UserService.get_all(
        db=db,
        skip=skip,
        limit=limit,
        role_id=role_id,
        email_verified=email_verified,
    )


@router.get("/user/{user_id}", response_model=UserWithRelations)
def read_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["users:read"])),
):
    """Get user by ID - Admin only"""
    user = UserService.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/user", response_model=UserResponse)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["users:create"])),
):
    """Create new user - Admin only"""
    try:
        new_user = UserService.create(db, user_data, current_user)
        return new_user
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/user/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["users:update"])),
):
    """Update user - Admin only"""
    try:
        updated_user = UserService.update(db, user_id, user_data, current_user)
        return updated_user
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/user/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["users:delete"])),
):
    """Delete user - Admin only"""
    try:
        UserService.delete(db, user_id, current_user)
        return {"message": "User deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/user/search", response_model=List[UserWithRelations])
def search_users(
    search_params: UserSearchParams,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["users:read"])),
):
    """Search users with various filters - Admin only"""
    return UserService.search_users(db, search_params)


@router.get("/user/stats/count")
def get_user_count(
    email_verified: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["users:read"])),
):
    """Count users - Admin only"""
    count = UserService.get_user_count(db, email_verified)
    return {"count": count}


# Admin manage user addresses
@router.get("/user/{user_id}/addresses", response_model=List[AddressResponse])
def admin_list_user_addresses(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["users:read"]))
):
    return AddressService.list_for_user(db, user_id)


@router.post("/user/{user_id}/addresses", response_model=AddressResponse)
def admin_create_user_address(
    user_id: int,
    data: AddressCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["users:update"]))
):
    return AddressService.create_for_user(db, user_id, data)


@router.put("/user/{user_id}/addresses/{address_id}", response_model=AddressResponse)
def admin_update_user_address(
    user_id: int,
    address_id: int,
    data: AddressUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["users:update"]))
):
    return AddressService.update_for_user(db, user_id, address_id, data)


@router.delete("/user/{user_id}/addresses/{address_id}")
def admin_delete_user_address(
    user_id: int,
    address_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["users:delete"]))
):
    AddressService.delete_for_user(db, user_id, address_id)
    return {"message": "Address deleted"}
