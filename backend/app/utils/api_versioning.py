"""
API Versioning Middleware
Handles API versioning with backward compatibility
"""

import logging
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import re

logger = logging.getLogger(__name__)

class APIVersioningMiddleware(BaseHTTPMiddleware):
    """
    Middleware for API versioning support
    Supports version negotiation via:
    - Accept header: application/vnd.signal-edge.v1+json
    - URL path: /api/v1/endpoint
    - Query parameter: ?version=v1
    """

    def __init__(self, app, default_version: str = "v1", supported_versions: Optional[list] = None):
        super().__init__(app)
        self.default_version = default_version
        self.supported_versions = supported_versions or ["v1"]
        self.version_mappings = {
            "v1": "v1",  # Current version
        }

    async def dispatch(self, request: Request, call_next):
        # Extract version from request
        version = self._extract_version(request)

        # Validate version
        if version and version not in self.supported_versions:
            return JSONResponse(
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
                content={
                    "error": "Unsupported API version",
                    "requested_version": version,
                    "supported_versions": self.supported_versions
                }
            )

        # Add version to request state for use in routes
        request.state.api_version = version or self.default_version

        # Continue with request
        response = await call_next(request)
        return response

    def _extract_version(self, request: Request) -> Optional[str]:
        """Extract API version from various sources"""

        # 1. URL path (highest priority)
        path_match = re.match(r"/api/(v\d+)/", request.url.path)
        if path_match:
            return path_match.group(1)

        # 2. Accept header
        accept_header = request.headers.get("accept", "")
        version_match = re.search(r"application/vnd\.signal-edge\.(\w+)\+json", accept_header)
        if version_match:
            return version_match.group(1)

        # 3. Query parameter
        version_param = request.query_params.get("version")
        if version_param:
            return version_param

        # 4. Custom header
        version_header = request.headers.get("x-api-version")
        if version_header:
            return version_header

        return None


def get_api_version(request: Request) -> str:
    """Get the API version from request state"""
    return getattr(request.state, 'api_version', 'v1')


def versioned_route(version: str, path: str):
    """Decorator to create versioned routes"""
    def decorator(func):
        func._api_version = version
        func._api_path = path
        return func
    return decorator


def setup_api_versioning(app, default_version: str = "v1", supported_versions: Optional[list] = None):
    """Setup API versioning middleware"""
    app.add_middleware(APIVersioningMiddleware,
                      default_version=default_version,
                      supported_versions=supported_versions)
    logger.info(f"✅ API versioning enabled (default: {default_version}, supported: {supported_versions})")