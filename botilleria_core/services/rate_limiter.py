from __future__ import annotations

import logging
import threading
import time

from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class RateLimiter:
    """Sliding Window Rate Limiter.

    Uses Redis sorted sets when a Redis client is available,
    and falls back to a thread-safe in-memory sliding window.
    """

    def __init__(self, redis_client: Redis | None = None) -> None:
        self.redis_client = redis_client
        self._in_memory_limits: dict[tuple[str, str], list[float]] = {}
        self._lock = threading.Lock()

    async def is_rate_limited(
        self,
        tenant_id: str,
        user_id: str,
        limit: int,
        window: int,
    ) -> bool:
        """Checks if a user under a specific tenant exceeds the rate limit.

        Args:
            tenant_id: Unique identifier for the tenant.
            user_id: Unique identifier for the user.
            limit: Maximum allowed requests within the window.
            window: Window size in seconds.

        Returns:
            bool: True if rate limit is exceeded, False otherwise.
        """
        if self.redis_client:
            key = f"ratelimit:{tenant_id}:{user_id}"
            now = time.time()
            cutoff = now - window
            try:
                pipe = self.redis_client.pipeline()
                pipe.zremrangebyscore(key, 0, cutoff)
                pipe.zadd(key, {str(now): now})
                pipe.zcard(key)
                pipe.expire(key, window)
                results = await pipe.execute()
                # results: [removed_count, added_count, total_count, expire_result]
                card: int = results[2]
                return card > limit
            except Exception as e:
                logger.error(
                    "Redis rate limiting failed. Falling back to in-memory: %s",
                    e,
                )

        # In-memory fallback
        now = time.time()
        cutoff = now - window
        key = (tenant_id, user_id)
        with self._lock:
            timestamps = self._in_memory_limits.get(key, [])
            # Prune old timestamps
            timestamps = [ts for ts in timestamps if ts > cutoff]
            timestamps.append(now)
            self._in_memory_limits[key] = timestamps
            return len(timestamps) > limit
