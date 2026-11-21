# backend/app/cache.py
import json
from typing import Any

from redis.asyncio import Redis
from redis.asyncio import from_url


class RedisCache:
    def __init__(self, redis_url: str = "redis://localhost:6379/0") -> None:
        self._redis_url = redis_url
        self._client: Redis | None = None

    async def connect(self) -> None:
        """Create the Redis client and verify the connection."""
        if self._client is None:
            client = from_url(
                self._redis_url,
                decode_responses=True,
                health_check_interval=30,
            )
            try:
                await client.ping()
            except Exception:
                await client.aclose()
                raise
            self._client = client

    async def close(self) -> None:
        """Close the Redis client and its connection pool."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def get(self, key: str) -> Any | None:
        """Return a decoded JSON value, or None if the key does not exist."""
        client = await self._get_client()
        data = await client.get(key)

        if data is None:
            return None

        return json.loads(data)

    async def set(
        self,
        key: str,
        value: Any,
        expire_seconds: int | None = 3600,
    ) -> None:
        """Store a JSON-serializable value; use None for no expiration."""
        if expire_seconds is not None and expire_seconds <= 0:
            raise ValueError("expire_seconds must be greater than 0 or None")

        client = await self._get_client()
        payload = json.dumps(value, ensure_ascii=False)
        await client.set(key, payload, ex=expire_seconds)

    async def delete(self, key: str) -> bool:
        """Delete a key; return True only if it existed."""
        client = await self._get_client()
        return bool(await client.delete(key))

    async def _get_client(self) -> Redis:
        if self._client is None:
            await self.connect()

        # connect() guarantees that _client is set.
        assert self._client is not None
        return self._client


cache = RedisCache()
