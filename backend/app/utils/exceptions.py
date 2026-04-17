"""
Custom Exceptions
Standardized error handling across the application
"""

from fastapi import HTTPException, status
from typing import Optional, Dict, Any

class ApplicationException(Exception):
    """
    Base application exception with structured error info
    """
    
    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        self.status_code = status_code
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API response"""
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details
            }
        }

class ValidationException(ApplicationException):
    """Exception for validation errors"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            details=details,
            status_code=status.HTTP_400_BAD_REQUEST
        )

class AuthenticationException(ApplicationException):
    """Exception for authentication errors"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR",
            status_code=status.HTTP_401_UNAUTHORIZED
        )

class AuthorizationException(ApplicationException):
    """Exception for authorization errors"""
    def __init__(self, message: str = "Access denied"):
        super().__init__(
            message=message,
            code="AUTHORIZATION_ERROR",
            status_code=status.HTTP_403_FORBIDDEN
        )

class ResourceNotFoundException(ApplicationException):
    """Exception for missing resources"""
    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            message=f"{resource_type} not found: {resource_id}",
            code="RESOURCE_NOT_FOUND",
            details={"resource_type": resource_type, "resource_id": resource_id},
            status_code=status.HTTP_404_NOT_FOUND
        )

class ExternalAPIException(ApplicationException):
    """Exception for external API failures"""
    def __init__(
        self,
        service: str,
        message: str,
        original_error: Optional[str] = None
    ):
        super().__init__(
            message=f"External service '{service}' error: {message}",
            code="EXTERNAL_API_ERROR",
            details={
                "service": service,
                "original_error": original_error
            },
            status_code=status.HTTP_502_BAD_GATEWAY
        )

class RateLimitException(ApplicationException):
    """Exception for rate limiting"""
    def __init__(self, retry_after: int):
        super().__init__(
            message=f"Rate limit exceeded. Retry after {retry_after} seconds.",
            code="RATE_LIMIT_EXCEEDED",
            details={"retry_after": retry_after},
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )

class MLModelException(ApplicationException):
    """Exception for ML model errors"""
    def __init__(
        self,
        model_key: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=f"ML Model '{model_key}' error: {message}",
            code="ML_MODEL_ERROR",
            details={
                "model_key": model_key,
                **(details or {})
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

class DatabaseException(ApplicationException):
    """Exception for database errors"""
    def __init__(self, message: str, original_error: Optional[str] = None):
        super().__init__(
            message=f"Database error: {message}",
            code="DATABASE_ERROR",
            details={"original_error": original_error},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

class CircuitBreakerOpenException(ApplicationException):
    """Exception when circuit breaker is open"""
    def __init__(self, service: str):
        super().__init__(
            message=f"Service '{service}' is temporarily unavailable",
            code="CIRCUIT_BREAKER_OPEN",
            details={"service": service},
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )

def setup_exception_handlers(app):
    """
    Setup FastAPI exception handlers
    """
    from fastapi import Request
    from fastapi.responses import JSONResponse
    import logging
    
    logger = logging.getLogger(__name__)
    
    @app.exception_handler(ApplicationException)
    async def handle_application_exception(request: Request, exc: ApplicationException):
        """Handle custom application exceptions"""
        logger.warning(f"Application exception: {exc.code} - {exc.message}")
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_dict()
        )
    
    @app.exception_handler(HTTPException)
    async def handle_http_exception(request: Request, exc: HTTPException):
        """Handle FastAPI HTTP exceptions"""
        logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": f"HTTP_{exc.status_code}",
                    "message": exc.detail
                }
            }
        )
    
    @app.exception_handler(Exception)
    async def handle_generic_exception(request: Request, exc: Exception):
        """Handle unexpected exceptions"""
        logger.error(f"Unexpected exception: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred"
                }
            }
        )
    
    logger.info("Exception handlers configured")
