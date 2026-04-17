"""
Comprehensive Logging Enhancement
Adds structured logging middleware and decorators for all services
"""

import logging
import time
import json
from functools import wraps
from typing import Any, Optional, Dict
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    Adds unique request IDs for request tracing
    """

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id") or str(uuid4())
        request.state.request_id = request_id

        # Log incoming request
        logger.info(
            "HTTP Request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host if request.client else "unknown",
            },
        )

        # Process request
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time

        # Log response
        logger.info(
            "HTTP Response",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": int(duration * 1000),
            },
        )

        # Add request ID to response headers
        response.headers["x-request-id"] = request_id
        return response


class PerformanceLoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs performance metrics for slow requests
    """

    SLOW_REQUEST_THRESHOLD = 1.0  # seconds

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time

        # Log slow requests
        if duration > self.SLOW_REQUEST_THRESHOLD:
            request_id = getattr(request.state, "request_id", "unknown")
            logger.warning(
                f"Slow request detected",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": int(duration * 1000),
                    "status_code": response.status_code,
                },
            )

        return response


class ErrorLoggingMiddleware(BaseHTTPMiddleware):
    """
    Captures and logs all errors with detailed context
    """

    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            request_id = getattr(request.state, "request_id", "unknown")
            logger.error(
                f"Request failed: {str(e)}",
                exc_info=True,
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "error_type": type(e).__name__,
                },
            )
            raise


def log_service_call(service_name: str, operation: str):
    """
    Decorator for logging service calls with timing
    Usage:
        @log_service_call("PaymentService", "process_subscription")
        async def process_subscription(...):
            ...
    """

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            func_args = str(args)[:100] if args else ""
            func_kwargs = str(kwargs)[:100] if kwargs else ""

            logger.info(
                f"Service call started",
                extra={
                    "service": service_name,
                    "operation": operation,
                    "args_preview": func_args,
                    "kwargs_preview": func_kwargs,
                },
            )

            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time

                logger.info(
                    f"Service call completed",
                    extra={
                        "service": service_name,
                        "operation": operation,
                        "duration_ms": int(duration * 1000),
                        "status": "success",
                    },
                )

                return result

            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"Service call failed: {str(e)}",
                    exc_info=True,
                    extra={
                        "service": service_name,
                        "operation": operation,
                        "duration_ms": int(duration * 1000),
                        "status": "failed",
                        "error_type": type(e).__name__,
                    },
                )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            func_args = str(args)[:100] if args else ""
            func_kwargs = str(kwargs)[:100] if kwargs else ""

            logger.info(
                f"Service call started",
                extra={
                    "service": service_name,
                    "operation": operation,
                    "args_preview": func_args,
                    "kwargs_preview": func_kwargs,
                },
            )

            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                logger.info(
                    f"Service call completed",
                    extra={
                        "service": service_name,
                        "operation": operation,
                        "duration_ms": int(duration * 1000),
                        "status": "success",
                    },
                )

                return result

            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"Service call failed: {str(e)}",
                    exc_info=True,
                    extra={
                        "service": service_name,
                        "operation": operation,
                        "duration_ms": int(duration * 1000),
                        "status": "failed",
                        "error_type": type(e).__name__,
                    },
                )
                raise

        # Return appropriate wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def log_database_query(query_name: str):
    """
    Decorator for logging database queries with timing
    Usage:
        @log_database_query("get_user_by_id")
        async def get_user_by_id(session, user_id):
            ...
    """

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()

            logger.debug(
                f"Database query started",
                extra={
                    "query_name": query_name,
                },
            )

            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time

                logger.debug(
                    f"Database query completed",
                    extra={
                        "query_name": query_name,
                        "duration_ms": int(duration * 1000),
                        "rows_returned": len(result) if isinstance(result, list) else 1,
                        "status": "success",
                    },
                )

                return result

            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"Database query failed: {str(e)}",
                    exc_info=True,
                    extra={
                        "query_name": query_name,
                        "duration_ms": int(duration * 1000),
                        "status": "failed",
                        "error_type": type(e).__name__,
                    },
                )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()

            logger.debug(
                f"Database query started",
                extra={
                    "query_name": query_name,
                },
            )

            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                logger.debug(
                    f"Database query completed",
                    extra={
                        "query_name": query_name,
                        "duration_ms": int(duration * 1000),
                        "rows_returned": len(result) if isinstance(result, list) else 1,
                        "status": "success",
                    },
                )

                return result

            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"Database query failed: {str(e)}",
                    exc_info=True,
                    extra={
                        "query_name": query_name,
                        "duration_ms": int(duration * 1000),
                        "status": "failed",
                        "error_type": type(e).__name__,
                    },
                )
                raise

        # Return appropriate wrapper
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def log_prediction_query(sport: str, prediction_type: str):
    """
    Decorator for logging prediction queries with sport context
    """

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()

            logger.debug(
                f"Prediction query started",
                extra={
                    "sport_key": sport,
                    "prediction_type": prediction_type,
                    "function": func.__name__,
                },
            )

            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time

                logger.info(
                    f"Prediction query completed",
                    extra={
                        "sport_key": sport,
                        "prediction_type": prediction_type,
                        "duration_ms": int(duration * 1000),
                        "predictions_returned": len(result) if isinstance(result, list) else 1,
                    },
                )

                return result

            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"Prediction query failed: {str(e)}",
                    exc_info=True,
                    extra={
                        "sport_key": sport,
                        "prediction_type": prediction_type,
                        "duration_ms": int(duration * 1000),
                        "error_type": type(e).__name__,
                    },
                )
                raise

        # Return appropriate wrapper
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return func

    return decorator


def setup_comprehensive_logging(app):
    """
    Setup all comprehensive logging middleware on FastAPI app
    """
    # Order matters - add in this order for proper request flow
    app.add_middleware(ErrorLoggingMiddleware)
    app.add_middleware(PerformanceLoggingMiddleware)
    app.add_middleware(RequestIdMiddleware)

    logger.info("Comprehensive logging middleware configured")


# Import asyncio at the end to avoid circular imports
import asyncio
