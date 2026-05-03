"""
Request Validation Middleware
Validates incoming requests and provides comprehensive input validation
"""

import logging
from typing import Dict, Any, Optional, List
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import json
import re

logger = logging.getLogger(__name__)

class ValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for comprehensive request validation
    """

    def __init__(self, app, exclude_paths: Optional[List[str]] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/health", "/ready", "/metrics"]

    async def dispatch(self, request: Request, call_next):
        # Skip validation for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        try:
            # Validate request method
            if request.method not in ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]:
                return JSONResponse(
                    status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                    content={"error": "Method not allowed", "method": request.method}
                )

            # Validate Content-Type for POST/PUT/PATCH
            if request.method in ["POST", "PUT", "PATCH"]:
                content_type = request.headers.get("content-type", "").lower()
                if not content_type:
                    return JSONResponse(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        content={"error": "Content-Type header required for this request"}
                    )

                # Allow JSON and form data
                if not (content_type.startswith("application/json") or
                       content_type.startswith("multipart/form-data") or
                       content_type.startswith("application/x-www-form-urlencoded")):
                    return JSONResponse(
                        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                        content={"error": "Unsupported content type", "content_type": content_type}
                    )

            # Validate Content-Length
            content_length = request.headers.get("content-length")
            if content_length:
                try:
                    length = int(content_length)
                    # Max 10MB for request body
                    if length > 10 * 1024 * 1024:
                        return JSONResponse(
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            content={"error": "Request too large", "max_size_mb": 10}
                        )
                except ValueError:
                    return JSONResponse(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        content={"error": "Invalid Content-Length header"}
                    )

            # Validate URL path
            if not self._is_valid_path(request.url.path):
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"error": "Invalid URL path"}
                )

            # Validate query parameters
            validation_error = self._validate_query_params(request.url.query)
            if validation_error:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"error": "Invalid query parameters", "details": validation_error}
                )

            # Validate headers
            header_error = self._validate_headers(request.headers)
            if header_error:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"error": "Invalid headers", "details": header_error}
                )

            # Continue with request
            response = await call_next(request)
            return response

        except Exception as e:
            logger.error(f"Validation middleware error: {e}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": "Validation error", "message": str(e)}
            )

    def _is_valid_path(self, path: str) -> bool:
        """Validate URL path for security"""
        # Basic path validation - no null bytes, directory traversal, etc.
        if "\x00" in path:  # Null bytes
            return False

        if ".." in path:  # Directory traversal
            return False

        # Only allow safe characters
        if not re.match(r"^[/a-zA-Z0-9._-]+$", path.replace("/", "")):
            return False

        return True

    def _validate_query_params(self, query_string: str) -> Optional[str]:
        """Validate query parameters"""
        if not query_string:
            return None

        try:
            # Parse query string manually for security
            params = {}
            for pair in query_string.split("&"):
                if "=" in pair:
                    key, value = pair.split("=", 1)
                    key = key.strip()
                    value = value.strip()

                    # Validate key
                    if not key or len(key) > 100:
                        return f"Invalid parameter key: {key}"

                    # Validate value
                    if len(value) > 1000:  # Max 1KB per parameter
                        return f"Parameter value too long: {key}"

                    # Check for suspicious content
                    if any(char in value for char in ["<", ">", "script", "javascript"]):
                        return f"Suspicious content in parameter: {key}"

                    params[key] = value

            return None

        except Exception as e:
            return f"Query parameter parsing error: {str(e)}"

    def _validate_headers(self, headers) -> Optional[str]:
        """Validate request headers"""
        # Check for required security headers
        suspicious_headers = ["x-forwarded-for", "x-real-ip"]

        for header_name in headers:
            header_lower = header_name.lower()

            # Check for suspicious headers that might indicate proxy abuse
            if header_lower in suspicious_headers:
                # Allow but log
                logger.warning(f"Suspicious header detected: {header_name}")

            # Validate header name
            if not re.match(r"^[a-zA-Z0-9_-]+$", header_name.replace("-", "")):
                return f"Invalid header name: {header_name}"

            # Validate header value length
            header_value = headers[header_name]
            if len(str(header_value)) > 4096:  # Max 4KB per header
                return f"Header value too long: {header_name}"

        return None


def setup_validation_middleware(app, exclude_paths: Optional[List[str]] = None):
    """Setup validation middleware for the FastAPI app"""
    app.add_middleware(ValidationMiddleware, exclude_paths=exclude_paths)
    logger.info("✅ Request validation middleware enabled")