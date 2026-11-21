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
        """اتصال ایمن به ردیس در صورت عدم وجود کلاینت فعال."""
        if self._client is None:
            try:
                self._client = redis.from_url(
                    self.redis_url, 
                    decode_responses=True,
                    encoding="utf-8"
                )
                # تست اتصال اولیه (اختیاری اما حرفه‌ای)
                await self._client.ping()
            except RedisError as e:
                logger.error(f"خطا در اتصال به ردیس: {e}")
                self._client = None
                raise

    async def close(self) -> None:
        """بستن ایمن اتصال ردیس."""
        if self._client:
            await self._client.close()
            self._client = None

    async def get(self, key: str) -> Optional[Any]:
        """دریافت مقدار از کش با مدیریت خطای JSON و Redis."""
        try:
            if not self._client:
                await self.connect()
            
            data = await self._client.get(key)
            if not data:
                return None
                
            return json.loads(data)
        except (RedisError, json.JSONDecodeError) as e:
            logger.warning(f"خطا در خواندن کلید {key} از کش: {e}")
            return None

    async def set(self, key: str, value: Any, expire_seconds: int = 3600) -> bool:
        """ذخیره مقدار در کش با تعیین زمان انقضا."""
        try:
            if not self._client:
                await self.connect()
                
            serialized_data = json.dumps(value, ensure_ascii=False)
            await self._client.set(key, serialized_data, ex=expire_seconds)
            return True
        except (RedisError, TypeError) as e:
            logger.error(f"خطا در نوشتن کلید {key} در کش: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """حذف یک کلید از کش (اضافه شده برای تکمیل قابلیت‌ها)."""
        try:
            if not self._client:
                await self.connect()
            await self._client.delete(key)
            return True
        except RedisError as e:
            logger.error(f"خطا در حذف کلید {key} از کش: {e}")
            return False

# نمونه سراسری (Singleton)
cache = RedisCache()
