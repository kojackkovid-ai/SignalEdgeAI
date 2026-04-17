"""
Error handling utilities and middleware
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from app.models.responses import ErrorResponse, APIException
from datetime import datetime
import uuid
import logging
import traceback

logger = logging.getLogger(__name__)


async def api_exception_handler(request: Request, exc: APIException):
    """Handle custom API exceptions with standardized response"""
    error_response = ErrorResponse(
        timestamp=datetime.utcnow(),
        status_code=exc.status_code,
        error_code=exc.error_code,
        message=exc.message,
        request_id=exc.request_id,
        details=exc.details if exc.details else None,
        path=str(request.url.path)
    )
    
    # Log the error
    log_level = "error" if exc.status_code >= 500 else "warning"
    getattr(logger, log_level)(
        f"{exc.error_code} | {exc.message} | Request: {request.method} {request.url.path} | User-Agent: {request.headers.get('user-agent', 'N/A')}"
    )
    
    # Convert to dict and serialize datetime to ISO format
    response_dict = error_response.dict(exclude_none=True)
    response_dict['timestamp'] = response_dict['timestamp'].isoformat() if isinstance(response_dict['timestamp'], datetime) else response_dict['timestamp']
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response_dict
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    request_id = str(uuid.uuid4())
    
    # Log full traceback for debugging
    logger.error(
        f"Unhandled exception | Request: {request.method} {request.url.path} | Request ID: {request_id}",
        exc_info=exc
    )
    
    error_response = ErrorResponse(
        timestamp=datetime.utcnow(),
        status_code=500,
        error_code="INTERNAL_ERROR",
        message="An unexpected error occurred",
        request_id=request_id,
        path=str(request.url.path)
    )
    
    # Convert to dict and serialize datetime to ISO format
    response_dict = error_response.dict(exclude_none=True)
    response_dict['timestamp'] = response_dict['timestamp'].isoformat() if isinstance(response_dict['timestamp'], datetime) else response_dict['timestamp']
    
    return JSONResponse(
        status_code=500,
        content=response_dict
    )


async def validation_error_handler(request: Request, exc: Exception):
    """Handle Pydantic validation errors"""
    request_id = str(uuid.uuid4())
    
    # Extract validation errors
    errors = []
    if hasattr(exc, 'errors'):
        for error in exc.errors():
            errors.append({
                "field": ".".join(str(x) for x in error["loc"][1:]),
                "error": error["msg"],
                "type": error["type"]
            })
    
    logger.warning(
        f"Validation error | Request: {request.method} {request.url.path} | Request ID: {request_id} | Errors: {errors}"
    )
    
    error_response = ErrorResponse(
        timestamp=datetime.utcnow(),
        status_code=422,
        error_code="VALIDATION_ERROR",
        message="Request validation failed",
        request_id=request_id,
        details={"validation_errors": errors},
        path=str(request.url.path)
    )
    
    # Convert to dict and serialize datetime to ISO format
    response_dict = error_response.dict(exclude_none=True)
    response_dict['timestamp'] = response_dict['timestamp'].isoformat() if isinstance(response_dict['timestamp'], datetime) else response_dict['timestamp']
    
    return JSONResponse(
        status_code=422,
        content=response_dict
    )


class ErrorHandlingMiddleware:
    """Middleware for consistent error handling"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        async def send_with_error_wrapper(message):
            if message["type"] == "http.response.start":
                # Could add custom error headers here
                pass
            await send(message)
        
        await self.app(scope, receive, send_with_error_wrapper)


def create_error_response(
    error_code: str,
    message: str,
    status_code: int = 400,
    details: dict = None,
    path: str = None
) -> dict:
    """Helper to create standardized error response dict"""
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "status_code": status_code,
        "error_code": error_code,
        "message": message,
        "request_id": str(uuid.uuid4()),
        "details": details,
        "path": path
    }


def log_error(
    error_code: str,
    message: str,
    exception: Exception = None,
    request: Request = None,
    level: str = "error"
):
    """Centralized error logging"""
    request_info = f" | Request: {request.method} {request.url.path}" if request else ""
    exc_info = exception if level == "error" else None
    
    log_message = f"{error_code} | {message}{request_info}"
    getattr(logger, level)(log_message, exc_info=exc_info)


def log_request(request: Request, response_status: int, response_time: float):
    """Log incoming request and response"""
    log_level = "info" if response_status < 400 else "warning" if response_status < 500 else "error"
    
    getattr(logger, log_level)(
        f"{request.method} {request.url.path} | Status: {response_status} | Time: {response_time:.3f}s"
    )
