"""
Enhanced Rate Limiting with Redis Support
Provides distributed rate limiting for scalability and performance
"""

import time
import asyncio
import logging
from typing import Dict, Optional, Tuple, Any
from functools import wraps
from datetime import datetime, timedelta
import json

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RateLimitExceeded(HTTPException):
    """Exception raised when rate limit is exceeded"""

    def __init__(self, retry_after: int):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Retry after {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)},
        )


class RedisRateLimiter:
    """
    Redis-backed rate limiter using token bucket algorithm
    Supports distributed rate limiting across multiple workers
    """

    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        self.enabled = redis_client is not None
        
        # Default rate limits (requests per minute)
        self.tier_limits = {
            "anonymous": 30,  # 0.5 req/sec
            "authenticated": 100,  # 1.67 req/sec
            "pro": 300,  # 5 req/sec
            "pro_plus": 600,  # 10 req/sec
            "elite": 1200,  # 20 req/sec
        }

    def _get_client_id(self, request: Request) -> str:
        """Extract unique client identifier from request"""
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            # Use token prefix as identifier (security: don't store full token)
            return f"user:{token[:32]}"

        # Fallback to IP address
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"

        return f"ip:{client_ip}"

    def _get_user_tier(self, request: Request) -> str:
        """Determine user tier from request token (if available)"""
        # In production, decode JWT and check subscription_tier
        # For now, default to authenticated if bearer token present
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            return "authenticated"
        return "anonymous"

    def _get_bucket_key(self, client_id: str, endpoint: Optional[str] = None) -> str:
        """Generate Redis key for rate limit bucket"""
        if endpoint:
            return f"ratelimit:{client_id}:{endpoint}"
        return f"ratelimit:{client_id}"

    async def check_rate_limit(
        self, request: Request, endpoint: Optional[str] = None
    ) -> Tuple[bool, int, Dict[str, Any]]:
        """
        Check if request is allowed under rate limit
        Returns (allowed, retry_after_seconds, rate_limit_info)
        """
        if not self.enabled:
            # If Redis unavailable, fall back to allowing all requests
            logger.warning("Rate limiter disabled - Redis unavailable")
            return True, 0, {
                "limit": "N/A",
                "remaining": "N/A",
                "reset": "N/A",
            }

        client_id = self._get_client_id(request)
        tier = self._get_user_tier(request)
        bucket_key = self._get_bucket_key(client_id, endpoint)
        
        try:
            limit = self.tier_limits.get(tier, self.tier_limits["anonymous"])
            window = 60  # 1 minute window

            # Get current bucket state
            bucket = self.redis_client.get(bucket_key)
            if asyncio.iscoroutine(bucket):
                bucket = await bucket

            if bucket:
                bucket_data = json.loads(bucket)
            else:
                bucket_data = {
                    "tokens": float(limit),
                    "last_reset": time.time(),
                }

            now = time.time()
            time_passed = now - bucket_data["last_reset"]

            # Refill tokens proportionally
            refill_rate = limit / window
            bucket_data["tokens"] = min(
                float(limit), 
                bucket_data["tokens"] + (time_passed * refill_rate)
            )
            bucket_data["last_reset"] = now

            # Check if request allowed
            if bucket_data["tokens"] >= 1.0:
                bucket_data["tokens"] -= 1.0
                allowed = True
                retry_after = 0
            else:
                allowed = False
                # Calculate when next token would be available
                retry_after = int((1.0 - bucket_data["tokens"]) / refill_rate) + 1

            # Store updated bucket (with expiration)
            set_result = self.redis_client.setex(
                bucket_key,
                window * 2,  # Expiration after 2 windows
                json.dumps(bucket_data),
            )
            if asyncio.iscoroutine(set_result):
                await set_result

            # Prepare rate limit info
            remaining = max(0, int(bucket_data["tokens"]))
            reset_time = int(bucket_data["last_reset"] + window)

            info = {
                "limit": limit,
                "remaining": remaining,
                "reset": reset_time,
                "tier": tier,
            }

            if not allowed:
                logger.warning(
                    f"Rate limit exceeded for {client_id} (tier: {tier}) "
                    f"on {endpoint or 'unspecified endpoint'}"
                )

            return allowed, retry_after, info

        except Exception as e:
            logger.error(f"Rate limiter error: {e} - allowing request")
            return True, 0, {
                "error": str(e),
            }


class EnhancedRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Enhanced middleware with Redis-backed rate limiting
    """

    def __init__(self, app, limiter: Optional[RedisRateLimiter] = None, exempt_paths=None):
        super().__init__(app)
        self.limiter = limiter or RedisRateLimiter()
        
        # Exempt paths from rate limiting
        self.exempt_paths = exempt_paths or [
            "/health",
            "/ready",
            "/docs",
            "/openapi.json",
            "/api/auth/login",
            "/api/auth/register",
            "/api/payment/webhook",  # Stripe webhooks
        ]

    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting"""
        path = request.url.path

        # Skip rate limiting for exempt paths
        if any(path.startswith(exempt) for exempt in self.exempt_paths):
            return await call_next(request)

        # Check rate limit
        allowed, retry_after, rate_info = await self.limiter.check_rate_limit(request, path)

        if not allowed:
            logger.warning(f"Rate limit exceeded: {path} - retry after {retry_after}s")
            raise RateLimitExceeded(retry_after)

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(rate_info.get("limit", "N/A"))
        response.headers["X-RateLimit-Remaining"] = str(rate_info.get("remaining", "N/A"))
        response.headers["X-RateLimit-Reset"] = str(rate_info.get("reset", "N/A"))

        return response


def setup_enhanced_rate_limiting(app, redis_client=None, exempt_paths=None):
    """Setup enhanced rate limiting middleware on FastAPI app"""
    limiter = RedisRateLimiter(redis_client)
    
    if limiter.enabled:
        logger.info("Enhanced rate limiting with Redis enabled")
    else:
        logger.warning("Redis not available - rate limiting disabled")

    app.add_middleware(
        EnhancedRateLimitMiddleware,
        limiter=limiter,
        exempt_paths=exempt_paths,
    )
