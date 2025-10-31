from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query , UploadFile , File , Form
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
    UserWithPerPage,
)
from app.schemas.address import AddressCreate, AddressUpdate, AddressResponse
from app.services.address_service import AddressService
from app.services.user_service import UserService
from app.deps.auth import (
    get_current_active_user,
    require_permission,
)

router = APIRouter()

@router.get("/me/profile", response_model=UserProfileBundle)
def read_my_profile_bundle(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get current user profile with addresses"""
    addresses = AddressService.list_for_user(db, current_user.id)
    return {"user": current_user, "addresses": addresses}

@router.post("/me/addresses", response_model=AddressResponse)
def create_my_address(
    data: AddressCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Create a new address for current user"""
    return AddressService.create_for_user(db, current_user, data)

@router.put("/me/addresses", response_model=AddressResponse)
def update_my_address(
    data: AddressUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update a specific address for current user"""
    return AddressService.update_for_user(db, current_user.id, data)


@router.delete("/me/addresses/{address_id}")
def delete_my_address(
    address_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete a specific address for current user"""
    AddressService.delete_for_user(db, current_user.id, address_id)
    return {"message": "Address deleted successfully"}


@router.get("/user", response_model=UserWithPerPage)
def read_users(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    role_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["users:read"])),
):
    """List users with optional filters - Admin only"""
    return UserService.get_all(
        db=db,
        page = page,
        limit=limit,
        role_id=role_id
    )


@router.get("/user/{user_id}", response_model=UserWithRelations)
def read_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["users:read"])),
):
    """Get user by ID - requires users:read permission"""
    user = UserService.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.post("/user", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    email: str = Form(...),
    password: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    role_id: int = Form(...),
    phone: Optional[str] = Form(None),
    picture: Optional[UploadFile] = File(None),
    address_type: Optional[str] = Form(None),
    label: Optional[str] = Form(None),
    recipient_name: Optional[str] = Form(None),
    company: Optional[str] = Form(None),
    street_address: Optional[str] = Form(None),
    apartment_suite: Optional[str] = Form(None),
    city: Optional[str] = Form(None),
    state: Optional[str] = Form(None),
    country: Optional[str] = Form(None),
    postal_code: Optional[str] = Form(None),
    longitude: Optional[float] = Form(None),
    latitude: Optional[float] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["users:create"])),
):
    """Create new user - requires users:create permission"""
    # ✅ Removed extra commas to avoid tuple creation
    userdata = UserCreate(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        role_id=role_id,
        phone=phone,
    )

    addressdata = AddressCreate(
        address_type=address_type,
        label=label,
        recipient_name=recipient_name,
        company=company,
        street_address=street_address,
        apartment_suite=apartment_suite,
        city=city,
        state=state,
        country=country,
        postal_code=postal_code,
        longitude=longitude,
        latitude=latitude,
    )

    try:
        new_user = UserService.create(
            db=db,
            user_data=userdata,
            address_data=addressdata,
            created_by=current_user,
            picture=picture,
        )
        return new_user
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))



@router.put("/user/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    email: Optional[str] = Form(None),
    first_name: Optional[str] = Form(None),
    last_name: Optional[str] = Form(None),
    role_id: Optional[int] = Form(None),
    phone: Optional[str] = Form(None),
    email_verified: Optional[bool] = Form(None),
    picture: Optional[UploadFile] = File(None),
    address_type: Optional[str] = Form(None),
    label: Optional[str] = Form(None),
    recipient_name: Optional[str] = Form(None),
    company: Optional[str] = Form(None),
    street_address: Optional[str] = Form(None),
    apartment_suite: Optional[str] = Form(None),
    city: Optional[str] = Form(None),
    state: Optional[str] = Form(None),
    country: Optional[str] = Form(None),
    postal_code: Optional[str] = Form(None),
    longitude: Optional[float] = Form(None),
    latitude: Optional[float] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["users:update"])),
):
    """Update user - requires users:update permission"""
    user_data = UserUpdate(
        email=email,
        first_name=first_name,
        last_name=last_name,
        role_id=role_id,
        phone=phone,
        email_verified=email_verified,
    )
    address_fields = [
        address_type, label, recipient_name, company, street_address,
        apartment_suite, city, state, country, postal_code, longitude, latitude
    ]
    address_data = None
    if any(address_fields):
        address_data = AddressUpdate(
            address_type = address_type,
            label=label,
            recipient_name = recipient_name,
            company = company,
            street_address = street_address,
            apartment_suite = apartment_suite,
            city = city,
            state = state,
            country = country,
            postal_code = postal_code,
            longitude = longitude,
            latitude = latitude,
        )
    try:
        updated_user = UserService.update(
            db = db, 
            user_id = user_id, 
            user_data = user_data, 
            address_data = address_data,
            updated_by = current_user,
            picture = picture
        )
        return updated_user
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/user/{user_id}", status_code=status.HTTP_200_OK)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["users:delete"])),
):
    """Delete user - requires users:delete permission"""
    try:
        UserService.delete(db, user_id, current_user)
        return {"message": "User deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/user/search", response_model=List[UserWithRelations])
def search_users(
    search_params: UserSearchParams,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["users:read"])),
):
    """Search users with various filters - requires users:read permission"""
    return UserService.search_users(db, search_params)


@router.get("/user/stats/count")
def get_user_count(
    email_verified: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["users:read"])),
):
    """Count users - requires users:read permission"""
    count = UserService.get_user_count(db, email_verified)
    return {"count": count, "email_verified": email_verified}


# Admin manage user addresses
@router.get("/user/{user_id}/addresses", response_model=List[AddressResponse])
def admin_list_user_addresses(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["users:read"]))
):
    """List all addresses for a specific user - requires users:read permission"""
    return AddressService.list_for_user(db, user_id)


@router.post("/user/{user_id}/addresses", response_model=AddressResponse, status_code=status.HTTP_201_CREATED)
def admin_create_user_address(
    user_id: int,
    data: AddressCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["users:update"]))
):
    """Create address for a specific user - requires users:update permission"""
    user = UserService.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return AddressService.create_for_user(db, user_id, data)


@router.put("/user/{user_id}/addresses/{address_id}", response_model=AddressResponse)
def admin_update_user_address(
    user_id: int,
    address_id: int,
    data: AddressUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["users:update"]))
):
    """Update address for a specific user - requires users:update permission"""
    return AddressService.update_for_user(db, user_id, address_id, data)


@router.delete("/user/{user_id}/addresses/{address_id}")
def admin_delete_user_address(
    user_id: int,
    address_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["users:delete"]))
):
    """Delete address for a specific user - requires users:delete permission"""
    AddressService.delete_for_user(db, user_id, address_id)
    return {"message": "Address deleted successfully"}
