from typing import Any, Optional, Union
import json
import pickle
from datetime import timedelta
import redis.asyncio as redis
from functools import wraps
import hashlib
import logging

logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis = redis.from_url(redis_url)
        self.default_ttl = timedelta(hours=1)

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            value = await self.redis.get(key)
            if value:
                return pickle.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[timedelta] = None) -> bool:
        """Set value in cache"""
        try:
            ttl = ttl or self.default_ttl
            serialized = pickle.dumps(value)
            return await self.redis.set(key, serialized, ex=int(ttl.total_seconds()))
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        try:
            return bool(await self.redis.delete(key))
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False

    async def clear(self) -> bool:
        """Clear all cache"""
        try:
            return bool(await self.redis.flushdb())
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False

def cache_key(*args, **kwargs) -> str:
    """Generate cache key from arguments"""
    key_parts = [str(arg) for arg in args]
    key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
    key_str = ":".join(key_parts)
    return hashlib.sha256(key_str.encode()).hexdigest()

def cached(ttl: Optional[timedelta] = None):
    """Decorator for caching function results"""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            if not hasattr(self, 'cache_manager'):
                return await func(self, *args, **kwargs)

            key = f"{func.__name__}:{cache_key(*args, **kwargs)}"
            result = await self.cache_manager.get(key)

            if result is not None:
                return result

            result = await func(self, *args, **kwargs)
            await self.cache_manager.set(key, result, ttl)
            return result
        return wrapper
    return decorator
