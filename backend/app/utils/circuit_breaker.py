"""
Circuit Breaker Pattern Implementation
Prevents cascading failures when external APIs are down
"""

import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, Optional, Any, Dict
from functools import wraps

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"         # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered

class CircuitBreaker:
    """
    Circuit breaker for external API calls.
    
    - CLOSED: Normal operation, requests pass through
    - OPEN: Service failing, requests fail immediately
    - HALF_OPEN: Testing if service recovered, limited requests allowed
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        half_open_max_calls: int = 3,
        expected_exception: type = Exception
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = timedelta(seconds=recovery_timeout)
        self.half_open_max_calls = half_open_max_calls
        self.expected_exception = expected_exception
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.half_open_calls = 0
        
        # Statistics
        self.total_calls = 0
        self.total_failures = 0
        self.total_successes = 0
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection
        """
        self.total_calls += 1
        
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                logger.info(f"[{self.name}] Circuit breaker entering HALF_OPEN state")
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
            else:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is OPEN. "
                    f"Last failure: {self.last_failure_time.isoformat() if self.last_failure_time else 'unknown'}"
                )
        
        if self.state == CircuitState.HALF_OPEN:
            if self.half_open_calls >= self.half_open_max_calls:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' HALF_OPEN limit reached"
                )
            self.half_open_calls += 1
        
        try:
            # Execute the function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # Success - handle state transition
            self._on_success()
            self.total_successes += 1
            return result
            
        except self.expected_exception as e:
            # Failure - handle state transition
            self._on_failure()
            self.total_failures += 1
            raise CircuitBreakerError(
                f"Circuit breaker '{self.name}' recorded failure: {str(e)}"
            ) from e
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to try recovery"""
        if self.last_failure_time is None:
            return True
        return datetime.utcnow() - self.last_failure_time >= self.recovery_timeout
    
    def _on_success(self):
        """Handle successful call"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.half_open_max_calls:
                logger.info(f"[{self.name}] Circuit breaker CLOSED (recovered)")
                self._reset()
        else:
            self.failure_count = 0
    
    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.state == CircuitState.HALF_OPEN:
            logger.warning(f"[{self.name}] Circuit breaker OPEN (recovery failed)")
            self.state = CircuitState.OPEN
        elif self.failure_count >= self.failure_threshold:
            logger.warning(
                f"[{self.name}] Circuit breaker OPEN after {self.failure_count} failures"
            )
            self.state = CircuitState.OPEN
    
    def _reset(self):
        """Reset circuit breaker to closed state"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.half_open_calls = 0
        self.last_failure_time = None
    
    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "total_calls": self.total_calls,
            "total_failures": self.total_failures,
            "total_successes": self.total_successes,
            "last_failure": self.last_failure_time.isoformat() if self.last_failure_time else None
        }

class CircuitBreakerError(Exception):
    """Base exception for circuit breaker errors"""
    pass

class CircuitBreakerOpenError(CircuitBreakerError):
    """Exception raised when circuit breaker is open"""
    pass

# Global circuit breakers registry
_circuit_breakers: Dict[str, CircuitBreaker] = {}

def get_circuit_breaker(name: str, **kwargs) -> CircuitBreaker:
    """Get or create a circuit breaker"""
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(name, **kwargs)
    return _circuit_breakers[name]

def circuit_breaker(name: str, **kwargs):
    """
    Decorator to apply circuit breaker to a function
    """
    def decorator(func):
        breaker = get_circuit_breaker(name, **kwargs)
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await breaker.call(func, *args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions in async context
            return breaker.call(func, *args, **kwargs)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator
