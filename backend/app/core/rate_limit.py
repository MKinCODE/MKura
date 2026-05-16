import redis.asyncio as redis
import logging
from typing import Optional
from .config import settings

# Add timeouts so it doesn't hang for 30s on invalid URLs like https://
try:
    rate_limit_redis = redis.from_url(
        settings.REDIS_URL, 
        decode_responses=True,
        socket_timeout=2.0,
        socket_connect_timeout=2.0
    )
except Exception as e:
    logging.warning(f"Failed to initialize Redis: {e}")
    rate_limit_redis = None


async def check_rate_limit(key: str, limit: int, window: int) -> tuple[bool, int]:
    if not rate_limit_redis:
        return True, limit

    try:
        current = await rate_limit_redis.get(key)
        if current is None:
            await rate_limit_redis.setex(key, window, 1)
            return True, limit - 1

        current_count = int(current)
        if current_count >= limit:
            return False, 0

        await rate_limit_redis.incr(key)
        return True, limit - current_count - 1
    except Exception as e:
        logging.warning(f"Redis rate limit error: {e}")
        # Fail open if Redis is down or URL is invalid
        return True, limit


async def increment_rate_limit(key: str, window: int):
    if not rate_limit_redis:
        return
        
    try:
        pipe = rate_limit_redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, window)
        await pipe.execute()
    except Exception as e:
        logging.warning(f"Redis increment error: {e}")