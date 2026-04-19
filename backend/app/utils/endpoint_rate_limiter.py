"""
Endpoint-Specific Rate Limiting Decorators
Applies rate limiting to specific endpoints without middleware interference
"""

import time
import logging
from typing import Dict, Tuple, Callable
from functools import wraps
from fastapi import Request, HTTPException, status

logger = logging.getLogger(__name__)


class TokenBucket:
    """Token bucket algorithm for rate limiting"""
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        Args:
            capacity: Maximum tokens in bucket
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = float(capacity)
        self.last_update = time.time()
    
    def consume(self, tokens: int = 1) -> Tuple[bool, int]:
        """
        Try to consume tokens. Returns (allowed, retry_after_seconds)
        """
        now = time.time()
        time_passed = now - self.last_update
        
        # Refill tokens based on time elapsed
        self.tokens = min(
            self.capacity,
            self.tokens + (time_passed * self.refill_rate)
        )
        self.last_update = now
        
        # Check if we have enough tokens
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True, 0
        
        # Calculate when next token will be available
        tokens_needed = tokens - self.tokens
        retry_after = int(tokens_needed / self.refill_rate) + 1
        return False, retry_after


class EndpointRateLimiter:
    """Rate limiter for specific endpoints"""
    
    def __init__(self):
        self.buckets: Dict[str, TokenBucket] = {}
    
    def _get_client_id(self, request: Request) -> str:
        """Extract unique identifier from request"""
        # Try JWT token first
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            return f"user:{token[:32]}"
        
        # Fall back to IP address
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"
        
        return f"ip:{client_ip}"
    
    def _get_bucket_key(self, client_id: str, endpoint: str) -> str:
        """Generate unique key for bucket"""
        return f"{endpoint}:{client_id}"
    
    def check_limit(
        self,
        request: Request,
        endpoint: str,
        requests: int,
        window: int
    ) -> Tuple[bool, int]:
        """
        Check if request is allowed. Returns (allowed, retry_after_seconds)
        Args:
            request: FastAPI request
            endpoint: Endpoint identifier
            requests: Max requests allowed
            window: Time window in seconds
        """
        client_id = self._get_client_id(request)
        bucket_key = self._get_bucket_key(client_id, endpoint)
        
        # Get or create bucket
        if bucket_key not in self.buckets:
            refill_rate = requests / window
            self.buckets[bucket_key] = TokenBucket(requests, refill_rate)
        
        bucket = self.buckets[bucket_key]
        return bucket.consume()


# Global limiter instance
endpoint_limiter = EndpointRateLimiter()


def rate_limit(endpoint: str, requests: int = 10, window: int = 60):
    """
    Decorator to apply rate limiting to a FastAPI endpoint
    
    Args:
        endpoint: Identifier for the endpoint (e.g., "auth:login")
        requests: Max requests allowed in window
        window: Time window in seconds
    
    Example:
        @router.post("/login")
        @rate_limit("auth:login", requests=5, window=900)  # 5 requests per 15 minutes
        async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Find the Request object in args first
            request_obj = None
            
            # Check positional args (http_request should be first param)
            for arg in args:
                if isinstance(arg, Request):
                    request_obj = arg
                    break
            
            # Check kwargs if not found in args
            if request_obj is None:
                for value in kwargs.values():
                    if isinstance(value, Request):
                        request_obj = value
                        break
            
            # If still not found, skip rate limiting
            if request_obj is None:
                logger.debug(f"Request object not found for {endpoint}")
                return await func(*args, **kwargs)
            
            # Check rate limit
            allowed, retry_after = endpoint_limiter.check_limit(
                request_obj,
                endpoint,
                requests,
                window
            )
            
            if not allowed:
                logger.warning(
                    f"Rate limit exceeded for {endpoint} - "
                    f"client: {endpoint_limiter._get_client_id(request_obj)} - "
                    f"retry after: {retry_after}s"
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Retry after {retry_after} seconds.",
                    headers={"Retry-After": str(retry_after)}
                )
            
            return await func(*args, **kwargs)
        
        return async_wrapper
    return decorator


def get_rate_limit_headers(request: Request, endpoint: str) -> Dict[str, str]:
    """Get rate limit info headers for a response"""
    client_id = endpoint_limiter._get_client_id(request)
    bucket_key = endpoint_limiter._get_bucket_key(client_id, endpoint)
    
    if bucket_key in endpoint_limiter.buckets:
        bucket = endpoint_limiter.buckets[bucket_key]
        return {
            "X-RateLimit-Limit": str(int(bucket.capacity)),
            "X-RateLimit-Remaining": str(max(0, int(bucket.tokens))),
            "X-RateLimit-Reset": str(int(bucket.last_update + (bucket.capacity / bucket.refill_rate))),
        }
    
    return {}
