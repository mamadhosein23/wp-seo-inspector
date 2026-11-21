import json
import logging
from typing import Any, Optional
import redis.asyncio as redis
from redis.asyncio import Redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)

class RedisCache:
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_url = redis_url
        self._client: Optional[Redis] = None

    async def connect(self) -> None:
        """Establish a secure connection to Redis."""
        if self._client is None:
            try:
                self._client = redis.from_url(
                    self.redis_url, 
                    decode_responses=True,
                    encoding="utf-8"
                )
                await self._client.ping()
            except RedisError as e:
                logger.error(f"Redis connection failed: {e}")
                self._client = None
                raise

    async def close(self) -> None:
        """Gracefully close the Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None

    async def get(self, key: str) -> Optional[Any]:
        """Fetch data with error handling for JSON and Redis."""
        try:
            if not self._client:
                await self.connect()
            
            data = await self._client.get(key)
            return json.loads(data) if data else None
        except (RedisError, json.JSONDecodeError) as e:
            logger.warning(f"Error fetching key '{key}' from cache: {e}")
            return None

    async def set(self, key: str, value: Any, expire_seconds: int = 3600) -> bool:
        """Store data in cache with TTL."""
        try:
            if not self._client:
                await self.connect()
                
            serialized_data = json.dumps(value, ensure_ascii=False)
            await self._client.set(key, serialized_data, ex=expire_seconds)
            return True
        except (RedisError, TypeError) as e:
            logger.error(f"Error setting key '{key}' in cache: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Remove a key from the cache."""
        try:
            if not self._client:
                await self.connect()
            await self._client.delete(key)
            return True
        except RedisError as e:
            logger.error(f"Error deleting key '{key}' from cache: {e}")
            return False

# Singleton instance
cache = RedisCache()
