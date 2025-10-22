
from ast import List
from nt import lseek
import re
from typing import Optional
from pydantic import field_validator , ValidationInfo
from app.core.exceptions import ValidationError ,ForbiddenException
from urllib.parse import urlparse

class BranchValidation:
    """Branch-related validation utilities."""
    @staticmethod
    def validate_branch_name(name: str) -> str:
        if not name:
            raise ValidationError("Branch name is required")
        if len(name) < 2:
            raise ValidationError("Branch name must be at least 2 characters long")
        
        if not re.match(r'^[a-zA-Z0-9_-]+$', name):
            raise ValidationError("Branch name can only contain letters, numbers, underscores, and hyphens")
        return name.lower()
    
    @staticmethod
    def validate_branch_description(description: Optional[str]) -> Optional[str]:
        if description and len(description) > 500:
            raise ValidationError("Branch description must be less than 500 characters long")
        return description.strip() if description else None
    
    @staticmethod
    def validate_branch_logo(logo: Optional[str]) -> Optional[str]:
        if logo:
            parsed = urlparse(logo)
            if not all([parsed.scheme, parsed.netloc]):
                raise ValidationError("Branch logo must be a valid URL")