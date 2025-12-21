from typing import Optional, Any, Dict
from fastapi import HTTPException, status


# -------------------------------
# Base Exception
# -------------------------------
class BaseAPIException(HTTPException):
    """Base API exception with an optional error code for consistency."""

    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code


# -------------------------------
# Authentication Exceptions
# -------------------------------
class InvalidCredentialsException(BaseAPIException):
    """Raised when username or password is invalid."""

    def __init__(self, detail: str = "Invalid username or password"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="INVALID_CREDENTIALS",
            headers={"WWW-Authenticate": "Bearer"},
        )


class TokenExpiredException(BaseAPIException):
    """Raised when a JWT token has expired."""

    def __init__(self, detail: str = "Token has expired"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="TOKEN_EXPIRED",
            headers={"WWW-Authenticate": "Bearer"},
        )


class InvalidTokenException(BaseAPIException):
    """Raised when a JWT token is invalid."""

    def __init__(self, detail: str = "Invalid authentication token"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="INVALID_TOKEN",
            headers={"WWW-Authenticate": "Bearer"},
        )


# -------------------------------
# Authorization Exceptions
# -------------------------------
class PermissionDeniedException(BaseAPIException):
    """Raised when a user lacks the required permission."""

    def __init__(self, detail: str = "You do not have permission to perform this action"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code="PERMISSION_DENIED",
        )


# -------------------------------
# Utility Exceptions
# -------------------------------
class ResourceNotFoundException(BaseAPIException):
    """Generic resource not found exception."""

    def __init__(self, detail: str = "Requested resource not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code="RESOURCE_NOT_FOUND",
        )


class BadRequestException(BaseAPIException):
    """Raised when a request is invalid."""

    def __init__(self, detail: str = "Bad request"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code="BAD_REQUEST",
        )


class ConflictException(BaseAPIException):
    """Raised when a resource conflict occurs (e.g., duplicate)."""

    def __init__(self, detail: str = "Resource conflict", resource_type: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            error_code="CONFLICT_ERROR",
        )
        self.resource_type = resource_type


class DatabaseError(BaseAPIException):
    """Raised when a database operation fails."""

    def __init__(self, detail: str = "Database operation failed"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code="DATABASE_ERROR",
        )


class RateLimitError(BaseAPIException):
    """Raised when rate limit is exceeded."""

    def __init__(self, detail: str = "Rate limit exceeded"):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            error_code="RATE_LIMIT_ERROR",
        )


class ExternalServiceError(BaseAPIException):
    """Raised when an external service fails."""

    def __init__(self, detail: str = "External service unavailable", service_name: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
            error_code="EXTERNAL_SERVICE_ERROR",
        )
        self.service_name = service_name

class ValidationError(BaseAPIException):
    """Raised when data validation fails."""

    def __init__(self, detail: str = "Validation error", field: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            error_code="VALIDATION_ERROR",
        )
        self.field = field


class NotFoundError(BaseAPIException):
    """Generic not found error with resource type."""

    def __init__(self, detail: str = "Resource not found", resource_type: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code="NOT_FOUND_ERROR",
        )
        self.resource_type = resource_type


class BankNotFoundError(NotFoundError):
    """Raised when a bank is not found."""

    def __init__(self, bank_id: Optional[int] = None):
        detail = f"Bank with ID {bank_id} not found" if bank_id else "Bank not found"
        super().__init__(detail=detail, resource_type="bank")


class ForbiddenException(HTTPException):
    """Generic 403 Forbidden error"""
    def __init__(self, detail: str = "You are not allowed to perform this action"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )