"""
Standardized error response models and exception handlers
"""

from pydantic import BaseModel
from typing import Optional, Any, Dict
from datetime import datetime
import uuid


class ErrorResponse(BaseModel):
    """Standardized error response for all API errors"""
    timestamp: datetime
    status_code: int
    error_code: str
    message: str
    request_id: str
    details: Optional[Dict[str, Any]] = None
    path: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "timestamp": "2026-03-08T15:30:00Z",
                "status_code": 400,
                "error_code": "INVALID_SPORT",
                "message": "The specified sport is not supported",
                "request_id": "req_abc123def456",
                "details": {
                    "provided": "xyz",
                    "valid_options": ["nba", "nhl", "mlb", "nfl", "soccer", "ncaab"]
                },
                "path": "/api/predictions/xyz"
            }
        }


class SuccessResponse(BaseModel):
    """Standardized success response template"""
    timestamp: datetime
    status_code: int
    data: Any
    message: str = "Success"
    request_id: str
    
    class Config:
        schema_extra = {
            "example": {
                "timestamp": "2026-03-08T15:30:00Z",
                "status_code": 200,
                "data": {"id": "pred_123", "sport": "nba"},
                "message": "Prediction retrieved successfully",
                "request_id": "req_abc123def456"
            }
        }


class PaginatedResponse(BaseModel):
    """Standardized paginated response"""
    timestamp: datetime
    status_code: int
    data: list
    pagination: Dict[str, Any]
    message: str = "Success"
    request_id: str
    
    class Config:
        schema_extra = {
            "example": {
                "timestamp": "2026-03-08T15:30:00Z",
                "status_code": 200,
                "data": [{"id": "pred_1"}, {"id": "pred_2"}],
                "pagination": {
                    "page": 1,
                    "per_page": 20,
                    "total": 100,
                    "total_pages": 5
                },
                "message": "Success",
                "request_id": "req_abc123def456"
            }
        }


# Exception classes
class APIException(Exception):
    """Base exception for API errors"""
    def __init__(
        self,
        error_code: str,
        message: str,
        status_code: int = 400,
        details: dict = None,
        path: str = None
    ):
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        self.path = path
        self.request_id = str(uuid.uuid4())


# Business Logic Errors
class InvalidSportError(APIException):
    def __init__(self, sport: str, valid_sports: list):
        super().__init__(
            error_code="INVALID_SPORT",
            message=f"Sport '{sport}' is not supported",
            status_code=400,
            details={"provided": sport, "valid_sports": valid_sports}
        )


class InvalidPredictionTypeError(APIException):
    def __init__(self, pred_type: str, valid_types: list):
        super().__init__(
            error_code="INVALID_PREDICTION_TYPE",
            message=f"Prediction type '{pred_type}' is not supported",
            status_code=400,
            details={"provided": pred_type, "valid_types": valid_types}
        )


class PredictionNotFoundError(APIException):
    def __init__(self, prediction_id: str):
        super().__init__(
            error_code="PREDICTION_NOT_FOUND",
            message=f"Prediction '{prediction_id}' not found",
            status_code=404,
            details={"prediction_id": prediction_id}
        )


# Authentication/Authorization Errors
class UnauthorizedError(APIException):
    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            error_code="UNAUTHORIZED",
            message=message,
            status_code=401,
            details={}
        )


class InvalidCredentialsError(APIException):
    def __init__(self):
        super().__init__(
            error_code="INVALID_CREDENTIALS",
            message="Invalid email or password",
            status_code=401,
            details={}
        )


class ForbiddenError(APIException):
    def __init__(self, message: str = "Access denied"):
        super().__init__(
            error_code="FORBIDDEN",
            message=message,
            status_code=403,
            details={}
        )


class TokenExpiredError(APIException):
    def __init__(self):
        super().__init__(
            error_code="TOKEN_EXPIRED",
            message="Your session has expired. Please log in again.",
            status_code=401,
            details={}
        )


class TokenRevokedError(APIException):
    def __init__(self):
        super().__init__(
            error_code="TOKEN_REVOKED",
            message="Your session has been revoked",
            status_code=401,
            details={}
        )


# Validation Errors
class ValidationError(APIException):
    def __init__(self, field: str, message: str):
        super().__init__(
            error_code="VALIDATION_ERROR",
            message=f"Validation failed for field '{field}'",
            status_code=400,
            details={"field": field, "error": message}
        )


class InvalidPayloadError(APIException):
    def __init__(self, message: str):
        super().__init__(
            error_code="INVALID_PAYLOAD",
            message="Request payload is invalid",
            status_code=400,
            details={"error": message}
        )


# Rate Limiting Errors
class RateLimitExceededError(APIException):
    def __init__(self, limit: int, reset_at: datetime):
        super().__init__(
            error_code="RATE_LIMIT_EXCEEDED",
            message="You have exceeded your rate limit",
            status_code=429,
            details={
                "limit": limit,
                "reset_at": reset_at.isoformat()
            }
        )


class DailyLimitExceededError(APIException):
    def __init__(self, limit: int, used: int, reset_at: datetime):
        super().__init__(
            error_code="DAILY_LIMIT_EXCEEDED",
            message="You have exceeded your daily prediction limit",
            status_code=429,
            details={
                "limit": limit,
                "used": used,
                "reset_at": reset_at.isoformat()
            }
        )


# Payment/Subscription Errors
class InsufficientCreditsError(APIException):
    def __init__(self, required: float, available: float):
        super().__init__(
            error_code="INSUFFICIENT_CREDITS",
            message="You don't have enough credits for this action",
            status_code=402,
            details={"required": required, "available": available}
        )


class SubscriptionRequiredError(APIException):
    def __init__(self, tier: str):
        super().__init__(
            error_code="SUBSCRIPTION_REQUIRED",
            message=f"This feature requires {tier} subscription",
            status_code=403,
            details={"required_tier": tier}
        )


class PaymentProcessingError(APIException):
    def __init__(self, message: str = "Payment processing failed"):
        super().__init__(
            error_code="PAYMENT_ERROR",
            message=message,
            status_code=400,
            details={}
        )


class InvalidPaymentMethodError(APIException):
    def __init__(self, reason: str = "Invalid payment method"):
        super().__init__(
            error_code="INVALID_PAYMENT_METHOD",
            message=reason,
            status_code=400,
            details={}
        )


# Resource Errors
class UserNotFoundError(APIException):
    def __init__(self, user_id: str):
        super().__init__(
            error_code="USER_NOT_FOUND",
            message=f"User '{user_id}' not found",
            status_code=404,
            details={"user_id": user_id}
        )


class DuplicateUserError(APIException):
    def __init__(self, email: str):
        super().__init__(
            error_code="DUPLICATE_USER",
            message=f"User with email '{email}' already exists",
            status_code=409,
            details={"email": email}
        )


class ResourceAlreadyExistsError(APIException):
    def __init__(self, resource_type: str, identifier: str):
        super().__init__(
            error_code="RESOURCE_ALREADY_EXISTS",
            message=f"{resource_type} '{identifier}' already exists",
            status_code=409,
            details={"type": resource_type, "identifier": identifier}
        )


# External Service Errors
class ESPNServiceError(APIException):
    def __init__(self, message: str = "ESPN API service unavailable"):
        super().__init__(
            error_code="EXTERNAL_SERVICE_ERROR",
            message=message,
            status_code=503,
            details={"service": "ESPN"}
        )


class MLServiceError(APIException):
    def __init__(self, message: str = "ML service temporarily unavailable"):
        super().__init__(
            error_code="ML_SERVICE_ERROR",
            message=message,
            status_code=503,
            details={"service": "ML"}
        )


class DatabaseError(APIException):
    def __init__(self, message: str = "Database service unavailable"):
        super().__init__(
            error_code="DATABASE_ERROR",
            message=message,
            status_code=503,
            details={}
        )


# Server Errors
class InternalServerError(APIException):
    def __init__(self, message: str = "Internal server error"):
        super().__init__(
            error_code="INTERNAL_ERROR",
            message=message,
            status_code=500,
            details={}
        )


class MethodNotAllowedError(APIException):
    def __init__(self, method: str, path: str):
        super().__init__(
            error_code="METHOD_NOT_ALLOWED",
            message=f"Method {method} is not allowed for {path}",
            status_code=405,
            details={"method": method, "path": path}
        )


class BadGatewayError(APIException):
    def __init__(self, message: str = "Bad gateway"):
        super().__init__(
            error_code="BAD_GATEWAY",
            message=message,
            status_code=502,
            details={}
        )
