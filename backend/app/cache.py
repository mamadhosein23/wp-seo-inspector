# backend/app/cache.py
import json
from typing import Optional
import redis.asyncio as redis
from redis.asyncio import Redis

class RedisCache:
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_url = redis_url
        self._client: Optional[Redis] = None

    async def connect(self):
        if not self._client:
            self._client = redis.from_url(self.redis_url, decode_responses=True)

    async def close(self):
        if self._client:
            await self._client.close()
            self._client = None

    async def get(self, key: str) -> Optional[dict]:
        if not self._client:
            await self.connect()
        data = await self._client.get(key)
        return json.loads(data) if data else None

    async def set(self, key: str, value: dict, expire_seconds: int = 3600):
        if not self._client:
            await self.connect()
        await self._client.set(key, json.dumps(value), ex=expire_seconds)

cache = RedisCache()
