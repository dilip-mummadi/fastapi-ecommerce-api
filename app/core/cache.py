"""Thin Redis wrapper used to cache expensive read endpoints (e.g. product listings).

Designed to fail open: if Redis is unreachable, the app keeps working without
caching rather than crashing. Swap REDIS_URL in .env to point anywhere.
"""
import json
from typing import Any

import redis.asyncio as redis

from app.core.config import settings

_pool: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _pool
    if _pool is None:
        _pool = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
    return _pool


async def cache_get(key: str) -> Any | None:
    try:
        client = get_redis()
        value = await client.get(key)
        return json.loads(value) if value else None
    except Exception:
        return None  # cache is best-effort; never break a request over it


async def cache_set(key: str, value: Any, ttl_seconds: int = 60) -> None:
    try:
        client = get_redis()
        await client.set(key, json.dumps(value, default=str), ex=ttl_seconds)
    except Exception:
        pass


async def cache_invalidate_prefix(prefix: str) -> None:
    try:
        client = get_redis()
        async for key in client.scan_iter(f"{prefix}*"):
            await client.delete(key)
    except Exception:
        pass
