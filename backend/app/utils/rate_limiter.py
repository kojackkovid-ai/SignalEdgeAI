"""
Rate Limiting Middleware
Prevents API abuse and ensures fair usage
"""

import time
import logging
from typing import Dict, Optional, Tuple, Callable
from functools import wraps
from datetime import datetime, timedelta

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

class RateLimitExceeded(HTTPException):
    """Exception raised when rate limit is exceeded"""
    def __init__(self, retry_after: int):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Retry after {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)}
        )

class TokenBucket:
    """
    Token bucket algorithm for rate limiting
    """
    
    def __init__(
        self,
        capacity: int,
        refill_rate: float,  # tokens per second
        key: str
    ):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.key = key
        
        self.tokens = float(capacity)
        self.last_update = time.time()
    
    def consume(self, tokens: int = 1) -> Tuple[bool, int]:
        """
        Try to consume tokens from the bucket.
        Returns (success, retry_after_seconds)
        """
        now = time.time()
        time_passed = now - self.last_update
        
        # Refill tokens
        self.tokens = min(
            self.capacity,
            self.tokens + time_passed * self.refill_rate
        )
        self.last_update = now
        
        # Check if we have enough tokens
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True, 0
        
        # Calculate retry after
        tokens_needed = tokens - self.tokens
        retry_after = int(tokens_needed / self.refill_rate) + 1
        
        return False, retry_after

class RateLimiter:
    """
    Rate limiter with multiple strategies
    """
    
    def __init__(self):
        self.buckets: Dict[str, TokenBucket] = {}
        self.default_limits = {
            "anonymous": (30, 0.1),      # 30 requests per 10 seconds
            "authenticated": (100, 0.5),  # 100 requests per 2 seconds
            "premium": (300, 1.0),        # 300 requests per second
        }
    
    def get_bucket_key(
        self,
        request: Request,
        tier: str = "anonymous",
        endpoint: Optional[str] = None
    ) -> str:
        """Generate unique key for rate limit bucket"""
        # Get client identifier
        client_id = self._get_client_id(request)
        
        # Include endpoint in key if specified
        if endpoint:
            return f"{client_id}:{endpoint}:{tier}"
        return f"{client_id}:{tier}"
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier from request"""
        # Try to get from JWT token
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            # Use token prefix as identifier (don't decode full token for performance)
            token = auth_header[7:]
            return f"user:{token[:16]}"
        
        # Fall back to IP address
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return f"ip:{forwarded.split(',')[0].strip()}"
        
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"
    
    def is_allowed(
        self,
        request: Request,
        tier: str = "anonymous",
        custom_limit: Optional[Tuple[int, float]] = None
    ) -> Tuple[bool, int]:
        """
        Check if request is allowed under rate limit
        Returns (allowed, retry_after_seconds)
        """
        key = self.get_bucket_key(request, tier)
        
        # Get or create bucket
        if key not in self.buckets:
            limit = custom_limit or self.default_limits.get(tier, self.default_limits["anonymous"])
            self.buckets[key] = TokenBucket(
                capacity=limit[0],
                refill_rate=limit[1],
                key=key
            )
        
        bucket = self.buckets[key]
        return bucket.consume()
    
    def limit(
        self,
        requests: int = 30,
        window: int = 60,
        tier: str = "anonymous"
    ):
        """
        Decorator to apply rate limiting to a function
        """
        refill_rate = requests / window
        
        def decorator(func: Callable):
            @wraps(func)
            async def async_wrapper(request: Request, *args, **kwargs):
                allowed, retry_after = self.is_allowed(
                    request,
                    tier=tier,
                    custom_limit=(requests, refill_rate)
                )
                
                if not allowed:
                    logger.warning(f"Rate limit exceeded for {self.get_bucket_key(request, tier)}")
                    raise RateLimitExceeded(retry_after)
                
                return await func(request, *args, **kwargs)
            
            return async_wrapper
        return decorator

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to apply rate limiting to all requests
    """
    
    def __init__(
        self,
        app,
        limiter: Optional[RateLimiter] = None,
        exempt_paths: Optional[list] = None
    ):
        super().__init__(app)
        self.limiter = limiter or RateLimiter()
        self.exempt_paths = exempt_paths or ["/health", "/docs", "/openapi.json"]
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting"""
        # Skip exempt paths
        path = request.url.path
        if any(path.startswith(exempt) for exempt in self.exempt_paths):
            return await call_next(request)
        
        # Determine tier based on auth
        tier = self._get_tier(request)
        
        # Check rate limit
        allowed, retry_after = self.limiter.is_allowed(request, tier=tier)
        
        if not allowed:
            logger.warning(f"Rate limit exceeded: {path} - tier: {tier}")
            raise RateLimitExceeded(retry_after)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        key = self.limiter.get_bucket_key(request, tier)
        bucket = self.limiter.buckets.get(key)
        if bucket:
            response.headers["X-RateLimit-Limit"] = str(bucket.capacity)
            response.headers["X-RateLimit-Remaining"] = str(int(bucket.tokens))
        
        return response
    
    def _get_tier(self, request: Request) -> str:
        """Determine user tier from request"""
        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            return "anonymous"
        
        # In a real implementation, decode JWT and check subscription tier
        # For now, assume authenticated users are "authenticated" tier
        return "authenticated"

# Global rate limiter instance
rate_limiter = RateLimiter()

def setup_rate_limiting(app, exempt_paths=None):
    """Setup rate limiting middleware on FastAPI app"""
    middleware = RateLimitMiddleware(app, rate_limiter, exempt_paths)
    app.add_middleware(RateLimitMiddleware, limiter=rate_limiter, exempt_paths=exempt_paths or [])
    logger.info("Rate limiting middleware configured")
