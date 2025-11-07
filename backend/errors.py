from typing import Optional, Any
from fastapi import HTTPException, status


class APIError(HTTPException):
    """Standardized API error response"""

    def __init__(
        self,
        status_code: int,
        message: str,
        code: Optional[str] = None,
        details: Optional[Any] = None
    ):
        self.code = code or f"ERROR_{status_code}"
        self.message = message
        self.details = details

        super().__init__(
            status_code=status_code,
            detail={
                "code": self.code,
                "message": self.message,
                "details": self.details
            }
        )


class ValidationError(APIError):
    """400 Bad Request - Validation errors"""

    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=message,
            code="VALIDATION_ERROR",
            details=details
        )


class ConflictError(APIError):
    """409 Conflict - Resource conflicts (e.g., double-booking)"""

    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            message=message,
            code="CONFLICT_ERROR",
            details=details
        )


class UnprocessableEntityError(APIError):
    """422 Unprocessable Entity - Business logic errors (e.g., invalid slot)"""

    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message=message,
            code="UNPROCESSABLE_ENTITY",
            details=details
        )


class NotFoundError(APIError):
    """404 Not Found"""

    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=message,
            code="NOT_FOUND",
            details=details
        )
