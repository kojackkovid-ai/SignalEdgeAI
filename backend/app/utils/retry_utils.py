"""
Retry Utilities for API Calls
Provides exponential backoff retry logic for failed requests.
"""

import asyncio
import logging
from typing import Callable, Any, Optional, TypeVar, Type
from functools import wraps
import httpx
import time

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryableError(Exception):
    """Base class for errors that should trigger a retry"""
    pass


class RateLimitError(RetryableError):
    """Error for rate limiting (429 responses)"""
    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message)
        self.retry_after = retry_after


class ServerError(RetryableError):
    """Error for server-side errors (5xx responses)"""
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.status_code = status_code


class TimeoutError(RetryableError):
    """Error for timeout issues"""
    pass


def calculate_backoff(attempt: int, base_delay: float = 1.0, max_delay: float = 60.0) -> float:
    """
    Calculate exponential backoff delay.
    
    Args:
        attempt: Current attempt number (0-indexed)
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        
    Returns:
        Delay in seconds
    """
    # Exponential backoff with jitter
    delay = min(base_delay * (2 ** attempt), max_delay)
    # Add jitter (±25%)
    import random
    jitter = delay * 0.25 * (2 * random.random() - 1)
    return delay + jitter


async def retry_async(
    func: Callable[..., Any],
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    retryable_exceptions: tuple = (httpx.HTTPError, asyncio.TimeoutError),
    non_retryable_exceptions: tuple = (),
    *args,
    **kwargs
) -> Any:
    """
    Retry an async function with exponential backoff.
    
    Args:
        func: Async function to retry
        max_attempts: Maximum number of attempts
        base_delay: Base delay between retries
        max_delay: Maximum delay between retries
        retryable_exceptions: Exceptions that trigger a retry
        non_retryable_exceptions: Exceptions that don't trigger a retry
        *args: Positional arguments for func
        **kwargs: Keyword arguments for func
        
    Returns:
        Result of func
        
    Raises:
        Last exception if all retries fail
    """
    last_exception = None
    
    for attempt in range(max_attempts):
        try:
            return await func(*args, **kwargs)
        except non_retryable_exceptions as e:
            # Don't retry for non-retryable exceptions
            logger.warning(f"Non-retryable error: {e}")
            raise
        except retryable_exceptions as e:
            last_exception = e
            
            if attempt < max_attempts - 1:
                delay = calculate_backoff(attempt, base_delay, max_delay)
                logger.warning(
                    f"Attempt {attempt + 1}/{max_attempts} failed: {e}. "
                    f"Retrying in {delay:.2f}s..."
                )
                await asyncio.sleep(delay)
            else:
                logger.error(f"All {max_attempts} attempts failed. Last error: {e}")
    
    raise last_exception


def create_retry_decorator(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0
):
    """
    Create a retry decorator for async functions.
    
    Args:
        max_attempts: Maximum number of attempts
        base_delay: Base delay between retries
        max_delay: Maximum delay between retries
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await retry_async(
                func,
                max_attempts=max_attempts,
                base_delay=base_delay,
                max_delay=max_delay,
                *args,
                **kwargs
            )
        return wrapper
    return decorator


class APIClientWithRetry:
    """
    HTTP client wrapper with built-in retry logic.
    """
    
    def __init__(
        self,
        client: httpx.AsyncClient,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0
    ):
        """
        Initialize the API client with retry logic.
        
        Args:
            client: httpx AsyncClient instance
            max_attempts: Maximum retry attempts
            base_delay: Base delay between retries
            max_delay: Maximum delay between retries
        """
        self.client = client
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
    
    async def get(
        self,
        url: str,
        *args,
        retry_on_status: tuple = (429, 500, 502, 503, 504),
        **kwargs
    ) -> httpx.Response:
        """
        GET request with retry logic.
        
        Args:
            url: URL to request
            *args: Additional positional arguments
            retry_on_status: HTTP status codes that trigger a retry
            **kwargs: Additional keyword arguments
            
        Returns:
            Response object
        """
        last_exception = None
        
        for attempt in range(self.max_attempts):
            try:
                response = await self.client.get(url, *args, **kwargs)
                
                # Check if we should retry based on status code
                if response.status_code in retry_on_status:
                    if attempt < self.max_attempts - 1:
                        delay = calculate_backoff(attempt, self.base_delay, self.max_delay)
                        
                        # Check for Retry-After header
                        retry_after = response.headers.get("Retry-After")
                        if retry_after:
                            try:
                                delay = max(delay, int(retry_after))
                            except ValueError:
                                pass
                        
                        logger.warning(
                            f"Got {response.status_code} on attempt {attempt + 1}/{self.max_attempts}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        await asyncio.sleep(delay)
                        continue
                    else:
                        raise ServerError(
                            f"Server error after {self.max_attempts} attempts",
                            response.status_code
                        )
                
                # Return successful response
                return response
                
            except httpx.TimeoutException as e:
                last_exception = e
                if attempt < self.max_attempts - 1:
                    delay = calculate_backoff(attempt, self.base_delay, self.max_delay)
                    logger.warning(f"Timeout on attempt {attempt + 1}. Retrying in {delay:.2f}s...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All {self.max_attempts} attempts timed out")
                    
            except httpx.ConnectError as e:
                last_exception = e
                if attempt < self.max_attempts - 1:
                    delay = calculate_backoff(attempt, self.base_delay, self.max_delay)
                    logger.warning(f"Connection error on attempt {attempt + 1}. Retrying in {delay:.2f}s...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All {self.max_attempts} attempts failed with connection error")
        
        raise last_exception
    
    async def post(
        self,
        url: str,
        *args,
        retry_on_status: tuple = (429, 500, 502, 503, 504),
        **kwargs
    ) -> httpx.Response:
        """
        POST request with retry logic.
        """
        return await self.get(url, *args, retry_on_status=retry_on_status, **kwargs)


def is_retryable_error(exception: Exception) -> bool:
    """
    Check if an exception is retryable.
    
    Args:
        exception: Exception to check
        
    Returns:
        True if the error is retryable
    """
    # Network errors
    if isinstance(exception, (httpx.ConnectError, httpx.TimeoutException)):
        return True
    
    # Server errors
    if isinstance(exception, httpx.HTTPStatusError):
        if exception.response.status_code in (429, 500, 502, 503, 504):
            return True
    
    return False

