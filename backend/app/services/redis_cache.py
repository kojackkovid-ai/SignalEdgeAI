"""
Redis Caching Service
Provides distributed caching for the sports prediction platform.
"""

import redis.asyncio as redis
import json
import logging
from typing import Optional, Any, Dict, List
from datetime import datetime, timedelta
import hashlib

logger = logging.getLogger(__name__)


class RedisCacheService:
    """
    Distributed Redis caching for predictions, games, and player stats.
    """
    
    # Cache key prefixes
    PREFIXES = {
        'games': 'games',
        'predictions': 'predictions',
        'player_props': 'player_props',
        'team_stats': 'team_stats',
        'player_stats': 'player_stats',
        'weather': 'weather',
        'odds': 'odds'
    }
    
    # TTL in seconds (5 minutes default)
    TTL = {
        'games': 300,           # 5 minutes
        'predictions': 300,     # 5 minutes
        'player_props': 600,    # 10 minutes
        'team_stats': 600,      # 10 minutes
        'player_stats': 900,    # 15 minutes
        'weather': 1800,        # 30 minutes
        'odds': 300             # 5 minutes
    }
    
    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize Redis connection.
        
        Args:
            redis_url: Redis connection URL (e.g., redis://localhost:6379)
        """
        self.redis_url = redis_url
        self._client: Optional[redis.Redis] = None
        self._connected = False
        
    async def connect(self) -> bool:
        """
        Connect to Redis server.
        
        Returns:
            True if connected successfully
        """
        if self._connected and self._client:
            return True
            
        try:
            if self.redis_url:
                self._client = redis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True
                )
            else:
                # Try environment variable
                import os
                redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
                self._client = redis.from_url(
                    redis_url,
                    encoding="utf-8",
                    decode_responses=True
                )
            
            # Test connection
            await self._client.ping()
            self._connected = True
            logger.info("Redis connection established successfully")
            return True
            
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Using in-memory fallback.")
            self._connected = False
            self._client = None
            return False
    
    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            self._connected = False
            logger.info("Redis connection closed")
    
    def _generate_key(self, prefix: str, *args) -> str:
        """
        Generate a cache key from prefix and arguments.
        
        Args:
            prefix: Key prefix (e.g., 'games', 'predictions')
            *args: Key components
            
        Returns:
            Cache key string
        """
        key_parts = [self.PREFIXES.get(prefix, prefix)]
        key_parts.extend(str(arg) for arg in args)
        key_string = ':'.join(key_parts)
        
        # Hash if too long
        if len(key_string) > 200:
            hash_suffix = hashlib.md5(key_string.encode()).hexdigest()[:16]
            return f"{self.PREFIXES.get(prefix, prefix)}:{hash_suffix}"
        
        return key_string
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        if not self._connected or not self._client:
            return None
            
        try:
            value = await self._client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.debug(f"Redis get error: {e}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (uses default if not provided)
            
        Returns:
            True if successful
        """
        if not self._connected or not self._client:
            return False
            
        try:
            ttl = ttl or 300  # Default 5 minutes
            serialized = json.dumps(value, default=str)
            await self._client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.debug(f"Redis set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if successful
        """
        if not self._connected or not self._client:
            return False
            
        try:
            await self._client.delete(key)
            return True
        except Exception as e:
            logger.debug(f"Redis delete error: {e}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern.
        
        Args:
            pattern: Key pattern (e.g., 'games:*')
            
        Returns:
            Number of keys deleted
        """
        if not self._connected or not self._client:
            return 0
            
        try:
            keys = []
            async for key in self._client.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                return await self._client.delete(*keys)
            return 0
        except Exception as e:
            logger.debug(f"Redis delete pattern error: {e}")
            return 0
    
    async def get_games(self, sport_key: str, date: str) -> Optional[List[Dict]]:
        """
        Get cached games for a sport and date.
        """
        key = self._generate_key('games', sport_key, date)
        return await self.get(key)
    
    async def set_games(
        self, 
        sport_key: str, 
        date: str, 
        games: List[Dict]
    ) -> bool:
        """
        Cache games for a sport and date.
        """
        key = self._generate_key('games', sport_key, date)
        return await self.set(key, games, self.TTL['games'])
    
    async def get_prediction(
        self, 
        sport_key: str, 
        event_id: str
    ) -> Optional[Dict]:
        """
        Get cached prediction.
        """
        key = self._generate_key('predictions', sport_key, event_id)
        return await self.get(key)
    
    async def set_prediction(
        self, 
        sport_key: str, 
        event_id: str, 
        prediction: Dict
    ) -> bool:
        """
        Cache prediction.
        """
        key = self._generate_key('predictions', sport_key, event_id)
        return await self.set(key, prediction, self.TTL['predictions'])
    
    async def get_player_props(
        self, 
        sport_key: str, 
        event_id: str
    ) -> Optional[List[Dict]]:
        """
        Get cached player props.
        """
        key = self._generate_key('player_props', sport_key, event_id)
        return await self.get(key)
    
    async def set_player_props(
        self, 
        sport_key: str, 
        event_id: str, 
        props: List[Dict]
    ) -> bool:
        """
        Cache player props.
        """
        key = self._generate_key('player_props', sport_key, event_id)
        return await self.set(key, props, self.TTL['player_props'])
    
    async def get_team_stats(
        self, 
        sport_key: str, 
        team_id: str
    ) -> Optional[Dict]:
        """
        Get cached team stats.
        """
        key = self._generate_key('team_stats', sport_key, team_id)
        return await self.get(key)
    
    async def set_team_stats(
        self, 
        sport_key: str, 
        team_id: str, 
        stats: Dict
    ) -> bool:
        """
        Cache team stats.
        """
        key = self._generate_key('team_stats', sport_key, team_id)
        return await self.set(key, stats, self.TTL['team_stats'])
    
    async def get_weather(
        self, 
        lat: float, 
        lon: float
    ) -> Optional[Dict]:
        """
        Get cached weather data.
        """
        key = self._generate_key('weather', f"{lat},{lon}")
        return await self.get(key)
    
    async def set_weather(
        self, 
        lat: float, 
        lon: float, 
        weather: Dict
    ) -> bool:
        """
        Cache weather data.
        """
        key = self._generate_key('weather', f"{lat},{lon}")
        return await self.set(key, weather, self.TTL['weather'])
    
    async def invalidate_sport(self, sport_key: str) -> int:
        """
        Invalidate all cache for a specific sport.
        
        Returns:
            Number of keys invalidated
        """
        patterns = [
            f"games:{sport_key}:*",
            f"predictions:{sport_key}:*",
            f"player_props:{sport_key}:*",
            f"team_stats:{sport_key}:*"
        ]
        
        total = 0
        for pattern in patterns:
            total += await self.delete_pattern(pattern)
        
        logger.info(f"Invalidated {total} cache entries for {sport_key}")
        return total
    
    async def get_stats(self) -> Dict:
        """
        Get Redis cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        if not self._connected or not self._client:
            return {
                'connected': False,
                'status': 'disconnected'
            }
        
        try:
            info = await self._client.info('stats')
            memory = await self._client.info('memory')
            
            return {
                'connected': True,
                'status': 'connected',
                'total_keys': await self._client.dbsize(),
                'hits': info.get('keyspace_hits', 0),
                'misses': info.get('keyspace_misses', 0),
                'memory_used': memory.get('used_memory_human', '0'),
                'uptime': info.get('uptime_in_days', 0)
            }
        except Exception as e:
            logger.error(f"Error getting Redis stats: {e}")
            return {
                'connected': False,
                'status': 'error',
                'error': str(e)
            }


class InMemoryCache:
    """
    Fallback in-memory cache when Redis is unavailable.
    """
    
    def __init__(self):
        self._cache: Dict[str, tuple] = {}  # key -> (timestamp, value)
        self._ttl = 300  # 5 minutes default
    
    def _is_expired(self, timestamp: float) -> bool:
        """Check if cache entry is expired."""
        return (datetime.now().timestamp() - timestamp) > self._ttl
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from in-memory cache."""
        if key in self._cache:
            timestamp, value = self._cache[key]
            if not self._is_expired(timestamp):
                return value
            else:
                del self._cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in in-memory cache."""
        self._cache[key] = (datetime.now().timestamp(), value)
        return True
    
    def delete(self, key: str) -> bool:
        """Delete key from in-memory cache."""
        if key in self._cache:
            del self._cache[key]
        return True
    
    def clear(self) -> None:
        """Clear all cache."""
        self._cache.clear()
