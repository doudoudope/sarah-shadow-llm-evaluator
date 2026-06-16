import redis.asyncio as aioredis

from app.config import settings

KEYS = ("shadow:total", "shadow:matches", "shadow:mismatches")


class MetricsStore:
    def __init__(self):
        self._redis = aioredis.from_url(settings.redis_url)

    async def record_match(self):
        async with self._redis.pipeline(transaction=True) as pipe:
            await pipe.incr("shadow:total").incr("shadow:matches").execute()

    async def record_mismatch(self):
        async with self._redis.pipeline(transaction=True) as pipe:
            await pipe.incr("shadow:total").incr("shadow:mismatches").execute()

    async def get_stats(self) -> dict:
        total, matches, mismatches = await self._redis.mget(*KEYS)
        total = int(total or 0)
        matches = int(matches or 0)
        mismatches = int(mismatches or 0)
        match_rate = round(matches / total * 100, 2) if total > 0 else 0.0
        return {
            "total_shadow_requests": total,
            "matches": matches,
            "mismatches": mismatches,
            "match_rate": match_rate,
        }

    async def reset(self):
        await self._redis.delete(*KEYS)

    async def close(self):
        await self._redis.aclose()


metrics = MetricsStore()
