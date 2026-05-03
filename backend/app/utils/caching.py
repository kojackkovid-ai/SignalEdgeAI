"""
Caching decorator and utilities for easy application to routes
Provides simple decorators for caching route responses
"""

import json
import hashlib
import logging
from functools import wraps
from typing import Callable, Optional, Any, Dict, List
from datetime import datetime, timedelta
import redis.asyncio as aioredis
from app.services.redis_cache import RedisCacheService
from app.config import settings

logger = logging.getLogger(__name__)

# Global cache service instance
_cache_service: Optional[RedisCacheService] = None


def get_redis_client(redis_url: Optional[str] = None):
    """Get a Redis client instance using the configured URL."""
    url = redis_url or settings.redis_url
    if not url:
        url = "redis://localhost:6379"
    return aioredis.from_url(url, encoding="utf-8", decode_responses=True)


async def init_cache_service(redis_url: Optional[str] = None) -> RedisCacheService:
    """Initialize global cache service"""
    global _cache_service
    _cache_service = RedisCacheService(redis_url)
    await _cache_service.connect()
    return _cache_service


async def get_cache_service() -> RedisCacheService:
    """Get global cache service instance"""
    global _cache_service
    if not _cache_service:
        _cache_service = RedisCacheService()
        await _cache_service.connect()
    return _cache_service


def generate_cache_key(
    prefix: str,
    identifier: str,
    params: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generate a cache key from a prefix, identifier, and optional parameters
    
    Args:
        prefix: Cache key prefix (e.g., 'predictions', 'player_props')
        identifier: Primary identifier (e.g., sport, user_id)
        params: Optional dict of parameters to include in key
        
    Returns:
        Cache key string
    """
    key_parts = [prefix, identifier]
    
    if params:
        # Sort params for consistent key generation
        sorted_params = sorted(params.items())
        for k, v in sorted_params:
            key_parts.append(f"{k}={v}")
    
    key_string = ":".join(str(p) for p in key_parts)
    
    # Hash if too long (Redis key limit is 512MB but practical limit much lower)
    if len(key_string) > 150:
        hash_suffix = hashlib.md5(key_string.encode()).hexdigest()[:16]
        return f"{prefix}:{hash_suffix}"
    
    return key_string


def cache_response(
    ttl: int = 300,
    prefix: str = "generic",
    key_builder: Optional[Callable] = None
):
    """
    Decorator to cache route responses
    
    Args:
        ttl: Time to live in seconds (default 5 minutes)
        prefix: Cache key prefix
        key_builder: Optional custom function to build cache key from args/kwargs
        
    Example:
        @cache_response(ttl=600, prefix="predictions")
        async def get_predictions(sport: str):
            return await db.get_predictions(sport)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                cache_service = await get_cache_service()
                
                # Generate cache key
                if key_builder:
                    cache_key = key_builder(*args, **kwargs)
                else:
                    # Default: use function name and kwargs that look like identifiers
                    identifiers = []
                    for k, v in sorted(kwargs.items()):
                        if k not in ['db', 'current_user', 'request', 'token']:
                            identifiers.append(f"{k}={v}")
                    
                    if identifiers:
                        cache_key = generate_cache_key(prefix, func.__name__, dict(kwargs))
                    else:
                        cache_key = f"{prefix}:{func.__name__}"
                
                # Try to get from cache
                cached = await cache_service.get(cache_key)
                if cached is not None:
                    logger.debug(f"Cache hit: {cache_key}")
                    return cached
                
                # Cache miss - call function
                result = await func(*args, **kwargs)
                
                # Store in cache
                await cache_service.set(cache_key, result, ttl)
                logger.debug(f"Cache set: {cache_key}")
                
                return result
                
            except Exception as e:
                logger.warning(f"Caching error for {func.__name__}: {e}")
                # On error, just call function without caching
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def invalidate_cache(pattern: str):
    """
    Decorator that invalidates cache matching pattern before executing
    
    Args:
        pattern: Cache key pattern to invalidate (e.g., "predictions:*")
        
    Example:
        @invalidate_cache(pattern="predictions:*")
        async def update_prediction(pred_id: str):
            # Cache will be cleared before this runs
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                cache_service = await get_cache_service()
                deleted = await cache_service.delete_pattern(pattern)
                logger.info(f"Invalidated {deleted} cache entries matching: {pattern}")
            except Exception as e:
                logger.warning(f"Cache invalidation error: {e}")
            
            # Execute function regardless of cache invalidation result
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


class CacheStrategy:
    """Cache strategy manager with configurable TTLs"""
    
    STRATEGIES = {
        'real_time': 60,           # 1 minute - for live data
        'live': 300,               # 5 minutes - frequent updates
        'recent': 600,             # 10 minutes - recent data
        'stable': 1800,            # 30 minutes - relatively stable
        'static': 3600 * 24,       # 24 hours - rarely changes
    }
    
    @classmethod
    def get_ttl(cls, strategy: str) -> int:
        """Get TTL for a strategy"""
        return cls.STRATEGIES.get(strategy, 300)
    
    @classmethod
    def cache_predictions(cls) -> int:
        """TTL for prediction data"""
        return cls.get_ttl('live')
    
    @classmethod
    def cache_player_props(cls) -> int:
        """TTL for player props"""
        return cls.get_ttl('live')
    
    @classmethod
    def cache_games(cls) -> int:
        """TTL for games/schedule"""
        return cls.get_ttl('stable')
    
    @classmethod
    def cache_user_data(cls) -> int:
        """TTL for user data"""
        return cls.get_ttl('recent')
    
    @classmethod
    def cache_stats(cls) -> int:
        """TTL for team/player stats"""
        return cls.get_ttl('recent')
    
    @classmethod
    def cache_odds(cls) -> int:
        """TTL for odds/lines"""
        return cls.get_ttl('real_time')


class CacheKeys:
    """Centralized cache key constants"""
    
    # Prediction keys
    PREDICTIONS_BY_SPORT = lambda sport: f"predictions:sport:{sport}"
    PREDICTIONS_BY_USER = lambda user_id: f"predictions:user:{user_id}"
    PREDICTION_DETAIL = lambda pred_id: f"prediction:detail:{pred_id}"
    
    # Player props keys
    PLAYER_PROPS_BY_SPORT = lambda sport: f"player_props:sport:{sport}"
    PLAYER_PROPS_BY_EVENT = lambda event_id: f"player_props:event:{event_id}"
    PLAYER_PROPS_DETAIL = lambda prop_id: f"player_prop:detail:{prop_id}"
    
    # Games/Events keys
    GAMES_BY_SPORT = lambda sport, date: f"games:sport:{sport}:date:{date}"
    GAMES_TODAY = lambda sport: f"games:sport:{sport}:today"
    UPCOMING_GAMES = lambda sport: f"games:sport:{sport}:upcoming"
    
    # User data keys
    USER_PROFILE = lambda user_id: f"user:profile:{user_id}"
    USER_SUBSCRIPTIONS = lambda user_id: f"user:subscriptions:{user_id}"
    USER_DAILY_LIMIT = lambda user_id: f"user:daily_limit:{user_id}"
    
    # Stats keys
    TEAM_STATS = lambda team_id: f"stats:team:{team_id}"
    PLAYER_STATS = lambda player_id: f"stats:player:{player_id}"
    
    # Odds keys
    GAME_ODDS = lambda game_id: f"odds:game:{game_id}"
    PROP_ODDS = lambda prop_id: f"odds:prop:{prop_id}"
    
    # Config keys
    TIER_CONFIG = lambda tier: f"config:tier:{tier}"
    APP_CONFIG = "config:app"
    
    # Invalidation patterns
    INVALIDATE_PREDICTIONS = "predictions:*"
    INVALIDATE_PROPS = "player_props:*"
    INVALIDATE_GAMES = "games:*"
    INVALIDATE_USER = lambda user_id: f"user:{user_id}:*"
    INVALIDATE_STATS = "stats:*"
    INVALIDATE_ODDS = "odds:*"


# Convenience functions for common cache operations
async def cache_get(key: str) -> Optional[Any]:
    """Get value from cache"""
    service = await get_cache_service()
    return await service.get(key)


async def cache_set(key: str, value: Any, ttl: int = 300) -> bool:
    """Set value in cache"""
    service = await get_cache_service()
    return await service.set(key, value, ttl)


async def cache_delete(key: str) -> bool:
    """Delete key from cache"""
    service = await get_cache_service()
    return await service.delete(key)


async def cache_invalidate(pattern: str) -> int:
    """Invalidate cache keys matching pattern"""
    service = await get_cache_service()
    return await service.delete_pattern(pattern)


async def cache_get_or_set(
    key: str,
    factory: Callable,
    ttl: int = 300
) -> Any:
    """Get from cache or call factory function to populate"""
    service = await get_cache_service()
    
    # Try cache first
    cached = await service.get(key)
    if cached is not None:
        return cached
    
    # Get from factory
    value = await factory() if callable(factory) else factory
    
    # Store in cache
    await service.set(key, value, ttl)
    
    return value
