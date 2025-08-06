"""
Caching utilities for performance optimization.
"""
import functools
import time
import json
import hashlib
import logging
from typing import Any, Callable, Dict, Optional, Union
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class MemoryCache:
    """Simple in-memory cache implementation."""
    
    def __init__(self, default_ttl: int = 3600):
        """
        Initialize memory cache.
        
        Args:
            default_ttl: Default time-to-live in seconds
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "expires": 0
        }
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        if key not in self._cache:
            self.stats["misses"] += 1
            return None
        
        cache_entry = self._cache[key]
        
        # Check if expired
        if cache_entry["expires_at"] < time.time():
            del self._cache[key]
            self.stats["expires"] += 1
            self.stats["misses"] += 1
            return None
        
        self.stats["hits"] += 1
        return cache_entry["value"]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        if ttl is None:
            ttl = self.default_ttl
        
        self._cache[key] = {
            "value": value,
            "expires_at": time.time() + ttl,
            "created_at": time.time()
        }
        self.stats["sets"] += 1
    
    def delete(self, key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key existed, False otherwise
        """
        if key in self._cache:
            del self._cache[key]
            self.stats["deletes"] += 1
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "expires": 0
        }
    
    def cleanup_expired(self) -> int:
        """
        Remove expired entries from cache.
        
        Returns:
            Number of expired entries removed
        """
        current_time = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry["expires_at"] < current_time
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        self.stats["expires"] += len(expired_keys)
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            **self.stats,
            "hit_rate": round(hit_rate, 2),
            "size": len(self._cache),
            "total_requests": total_requests
        }
    
    def keys(self) -> list:
        """Get all cache keys."""
        return list(self._cache.keys())
    
    def exists(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        return self.get(key) is not None


# Global cache instance
cache = MemoryCache(default_ttl=3600)  # 1 hour default TTL


def cache_key(*args, **kwargs) -> str:
    """
    Generate cache key from function arguments.
    
    Args:
        *args: Function positional arguments
        **kwargs: Function keyword arguments
        
    Returns:
        Cache key string
    """
    # Create a string representation of arguments
    key_parts = []
    
    # Add positional arguments
    for arg in args:
        if hasattr(arg, 'id'):  # Database models
            key_parts.append(f"{type(arg).__name__}:{arg.id}")
        else:
            key_parts.append(str(arg))
    
    # Add keyword arguments
    for k, v in sorted(kwargs.items()):
        if hasattr(v, 'id'):  # Database models
            key_parts.append(f"{k}={type(v).__name__}:{v.id}")
        else:
            key_parts.append(f"{k}={v}")
    
    # Create hash of the key parts
    key_string = "|".join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()


def cached(ttl: int = 3600, key_prefix: str = ""):
    """
    Decorator for caching function results.
    
    Args:
        ttl: Cache time-to-live in seconds
        key_prefix: Optional prefix for cache keys
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            func_name = f"{func.__module__}.{func.__name__}"
            key = f"{key_prefix}{func_name}:{cache_key(*args, **kwargs)}"
            
            # Try to get from cache
            cached_result = cache.get(key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func_name}")
                return cached_result
            
            # Execute function and cache result
            logger.debug(f"Cache miss for {func_name}, executing function")
            result = func(*args, **kwargs)
            cache.set(key, result, ttl)
            
            return result
        
        # Add cache management methods to the wrapper
        wrapper.cache_clear = lambda: cache.clear()
        wrapper.cache_stats = lambda: cache.get_stats()
        wrapper.cache_info = wrapper.cache_stats  # Compatibility with functools.lru_cache
        
        return wrapper
    return decorator


def cache_result(ttl: int = 3600):
    """
    Simple cache decorator with TTL.
    
    Args:
        ttl: Cache time-to-live in seconds
        
    Returns:
        Decorated function
    """
    return cached(ttl=ttl)


class CacheManager:
    """Cache management utilities."""
    
    @staticmethod
    def get_cache_stats() -> Dict[str, Any]:
        """Get global cache statistics."""
        return cache.get_stats()
    
    @staticmethod
    def clear_cache() -> None:
        """Clear all cache entries."""
        cache.clear()
        logger.info("Cache cleared")
    
    @staticmethod
    def cleanup_expired() -> int:
        """Remove expired entries from cache."""
        count = cache.cleanup_expired()
        if count > 0:
            logger.info(f"Cleaned up {count} expired cache entries")
        return count
    
    @staticmethod
    def invalidate_pattern(pattern: str) -> int:
        """
        Invalidate cache entries matching a pattern.
        
        Args:
            pattern: Pattern to match (simple string contains)
            
        Returns:
            Number of entries invalidated
        """
        keys_to_delete = [
            key for key in cache.keys()
            if pattern in key
        ]
        
        count = 0
        for key in keys_to_delete:
            if cache.delete(key):
                count += 1
        
        if count > 0:
            logger.info(f"Invalidated {count} cache entries matching pattern: {pattern}")
        
        return count
    
    @staticmethod
    def get_cache_info() -> Dict[str, Any]:
        """Get detailed cache information."""
        stats = cache.get_stats()
        
        # Calculate memory usage estimation
        memory_usage = 0
        entry_details = []
        
        for key in cache.keys():
            entry = cache._cache[key]
            entry_size = len(str(entry["value"]))  # Rough estimate
            memory_usage += entry_size
            
            entry_details.append({
                "key": key,
                "size_estimate": entry_size,
                "created_at": datetime.fromtimestamp(entry["created_at"]).isoformat(),
                "expires_at": datetime.fromtimestamp(entry["expires_at"]).isoformat(),
                "ttl_remaining": max(0, entry["expires_at"] - time.time())
            })
        
        return {
            "stats": stats,
            "memory_usage_estimate": memory_usage,
            "entries": entry_details
        }


# Specialized cache decorators for common use cases

def cache_database_query(ttl: int = 1800):
    """
    Cache decorator for database queries (30 minutes default).
    
    Args:
        ttl: Cache time-to-live in seconds
        
    Returns:
        Decorated function
    """
    return cached(ttl=ttl, key_prefix="db:")


def cache_api_response(ttl: int = 300):
    """
    Cache decorator for API responses (5 minutes default).
    
    Args:
        ttl: Cache time-to-live in seconds
        
    Returns:
        Decorated function
    """
    return cached(ttl=ttl, key_prefix="api:")


def cache_computation(ttl: int = 3600):
    """
    Cache decorator for expensive computations (1 hour default).
    
    Args:
        ttl: Cache time-to-live in seconds
        
    Returns:
        Decorated function
    """
    return cached(ttl=ttl, key_prefix="compute:")


def cache_file_operation(ttl: int = 600):
    """
    Cache decorator for file operations (10 minutes default).
    
    Args:
        ttl: Cache time-to-live in seconds
        
    Returns:
        Decorated function
    """
    return cached(ttl=ttl, key_prefix="file:")


# Background task for cache maintenance
def setup_cache_maintenance():
    """Setup background cache maintenance."""
    import threading
    import time
    
    def cleanup_task():
        while True:
            try:
                cache.cleanup_expired()
                time.sleep(300)  # Run every 5 minutes
            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")
                time.sleep(60)  # Wait 1 minute before retry
    
    cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
    cleanup_thread.start()
    logger.info("Cache maintenance thread started")


# Example usage patterns
if __name__ == "__main__":
    # Example of using the cache decorator
    @cache_result(ttl=300)
    def expensive_operation(param1: str, param2: int) -> str:
        """Simulate an expensive operation."""
        import time
        time.sleep(1)  # Simulate work
        return f"Result for {param1} and {param2}"
    
    # Test cache functionality
    print("First call (should take 1 second):")
    start = time.time()
    result1 = expensive_operation("test", 42)
    print(f"Result: {result1}, Time: {time.time() - start:.2f}s")
    
    print("\nSecond call (should be instant from cache):")
    start = time.time()
    result2 = expensive_operation("test", 42)
    print(f"Result: {result2}, Time: {time.time() - start:.2f}s")
    
    print(f"\nCache stats: {cache.get_stats()}")