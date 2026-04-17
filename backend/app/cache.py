"""
Cache Manager for Sports Prediction Platform
Handles caching of scraped data to prevent excessive requests and improve performance
"""

import time
import logging
from typing import Optional, Any, Dict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class CacheManager:
    """
    Simple in-memory cache manager with TTL support
    Can be extended to support Redis for distributed caching
    """
    
    def __init__(self, ttl_minutes: int = 30):
        """
        Initialize cache manager
        
        Args:
            ttl_minutes: Time-to-live in minutes for cached entries
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl_seconds = ttl_minutes * 60
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache if it exists and hasn't expired
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        if time.time() > entry['expires_at']:
            # Entry has expired, remove it
            del self.cache[key]
            return None
        
        logger.debug(f"Cache HIT for key: {key}")
        return entry['value']
    
    def set(self, key: str, value: Any, ttl_minutes: Optional[int] = None):
        """
        Set value in cache with TTL
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_minutes: Optional override for TTL (uses default if not specified)
        """
        ttl = ttl_minutes * 60 if ttl_minutes else self.ttl_seconds
        self.cache[key] = {
            'value': value,
            'expires_at': time.time() + ttl,
            'created_at': time.time()
        }
        logger.debug(f"Cache SET for key: {key}, TTL: {ttl} seconds")
    
    def clear(self, pattern: Optional[str] = None):
        """
        Clear cache entries
        
        Args:
            pattern: Optional pattern to match keys (simple substring match)
                    If None, clears entire cache
        """
        if pattern is None:
            self.cache.clear()
            logger.info("Cache cleared (all entries)")
        else:
            keys_to_delete = [k for k in self.cache.keys() if pattern in k]
            for key in keys_to_delete:
                del self.cache[key]
            logger.info(f"Cache cleared ({len(keys_to_delete)} entries matching '{pattern}')")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache stats
        """
        total_entries = len(self.cache)
        expired_entries = sum(1 for entry in self.cache.values() if time.time() > entry['expires_at'])
        valid_entries = total_entries - expired_entries
        
        return {
            'total_entries': total_entries,
            'valid_entries': valid_entries,
            'expired_entries': expired_entries,
            'ttl_seconds': self.ttl_seconds
        }

# Global cache manager instance
cache_manager = CacheManager(ttl_minutes=30)
