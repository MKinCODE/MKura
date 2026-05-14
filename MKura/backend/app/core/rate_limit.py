import redis.asyncio as redis
from typing import Optional
from .config import settings

rate_limit_redis = redis.from_url(settings.REDIS_URL, decode_responses=True)


async def check_rate_limit(key: str, limit: int, window: int) -> tuple[bool, int]:
    current = await rate_limit_redis.get(key)
    if current is None:
        await rate_limit_redis.setex(key, window, 1)
        return True, limit - 1

    current_count = int(current)
    if current_count >= limit:
        return False, 0

    await rate_limit_redis.incr(key)
    return True, limit - current_count - 1


async def increment_rate_limit(key: str, window: int):
    pipe = rate_limit_redis.pipeline()
    pipe.incr(key)
    pipe.expire(key, window)
    await pipe.execute()