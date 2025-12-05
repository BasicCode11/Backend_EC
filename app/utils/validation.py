import re 
from typing import Any, Optional
from app.core.exceptions import ValidationError, ForbiddenException
from urllib.parse import urlparse

class CommonValidation:
    """Common validation utilities."""
    @staticmethod
    def validate_email(email: str) -> str:
        if not email:
            raise ValidationError("Email is required")
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            raise ValidationError("Invalid email address")
        return email

    @staticmethod
    def validate_password(password: str) -> str:
        if not password:
            raise ValidationError("Password is required")
        if len(password) < 6:
            raise ValidationError("Password must be at least 6 characters long")
        if len(password) > 15:
            raise ValidationError("Password must be less than 10 characters long")
        return password
    
    @staticmethod
    def validate_phone(phone: str) -> str:
        # Return None if phone is not required
        if phone is None or phone.strip() == "":
            return phone

        phone = phone.strip()
        pattern = r"^\+?\d{7,15}$"  # Allows digits with optional + and length 7–15
        if not re.match(pattern, phone):
            raise ValidationError(f"Invalid phone number format: {phone}")
        return phone

    @staticmethod
    def validate_user_has_role(user_roles: None | list[str]) -> list[str]:
        """
        Ensure user has at least one role.
        Example: ["admin", "manager"]
        """
        if not user_roles or len(user_roles) == 0:
            raise ForbiddenException("User must have at least one role assigned")  # pyright: ignore[reportUndefinedVariable]

        # Optionally: normalize roles to lowercase
        return [role.lower() for role in user_roles]

class TeamValidation:
    """Team-related validation utilities."""

    @staticmethod
    def validate_team_name(name: str) -> str:
        if not name:
            raise ValidationError("Team name is required")
        if len(name) < 2:
            raise ValidationError("Team name must be at least 2 characters long")
        if len(name) > 100:
            raise ValidationError("Team name must be less than 100 characters long")
        return name.strip()

    @staticmethod
    def validate_team_description(description: Optional[str]) -> Optional[str]:
        if description and len(description) > 500:
            raise ValidationError("Team description must be less than 500 characters long")
        return description.strip() if description else None
    
class ProductValidation:
    """Product-related validation utilities."""

    @staticmethod
    def validate_product_name(name: str) -> str:
        if not name:
            raise ValidationError("Product name is required")
        if len(name) < 2:
            raise ValidationError("Product name must be at least 2 characters long")
        if len(name) > 100:
            raise ValidationError("Product name must be less than 100 characters long")
        return name.strip()
    @staticmethod
    def validate_product_description(description: Optional[str]) -> Optional[str]:
        if description and len(description) > 500:
            raise ValidationError("Product description must be less than 500 characters long")
        return description.strip() if description else None
    
    @staticmethod
    def validate_product_is_active(is_active: Optional[bool]) -> bool:
        return is_active if is_active is not None else True
    
    @staticmethod
    def validate_product_logo(logo: Optional[str]) -> Optional[str]:
        if logo:
            parsed = urlparse(logo)
            if not all([parsed.scheme, parsed.netloc]):
                raise ValidationError("Product logo must be a valid URL")
            if len(logo) > 255:
                raise ValidationError("Product logo URL must be less than 255 characters long")
            return logo.strip()
        return None
    
    @staticmethod
    def validate_product_team_id(team_id: int) -> int:
        if team_id <= 0:
            raise ValidationError("Team ID must be a positive integer")
        return team_id
    

class RoleValidation:
    """Role-related validation utilities."""

    @staticmethod
    def validate_role_name(name: str) -> str:
        if not name:
            raise ValidationError("Role name is required")
        if len(name) < 2:
            raise ValidationError("Role name must be at least 2 characters long")
        if len(name) > 100:
            raise ValidationError("Role name must be less than 100 characters long")
        return name.strip()

    @staticmethod
    def validate_description(description: Optional[str]) -> Optional[str]:
        if description and len(description) > 500:
            raise ValidationError("Role description must be less than 500 characters long")
        return description.strip() if description else None
    

