import asyncio
import json
import logging
from collections.abc import Callable, Coroutine
from typing import Any

from redis.asyncio import Redis

from app.core.config import settings

logger = logging.getLogger(__name__)


def _safe_parse(value: str) -> Any | None:
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError) as err:
        logger.warning("Cache parse failed, ignoring entry: %s", err)
        return None


async def get(key: str, redis: Redis) -> Any | None:
    try:
        data = await redis.get(key)
        if not data:
            return None
        text = data.decode() if isinstance(data, bytes) else data
        return _safe_parse(text)
    except Exception as err:
        logger.warning("Redis GET failed, bypassing cache: %s", err)
        return None


async def set(
    key: str, value: Any, redis: Redis, ttl: int = settings.CACHE_TTL
) -> None:
    try:
        await redis.set(key, json.dumps(value), ex=ttl)
    except Exception as err:
        logger.warning("Redis SET failed, skipping cache: %s", err)


async def wrap(
    key: str,
    fn: Callable[[], Coroutine[Any, Any, Any]],
    redis: Redis,
    ttl: int = settings.CACHE_TTL,
) -> dict[str, Any]:
    cached = await get(key, redis)
    if cached is not None:
        return {"data": cached, "from_cache": True}

    fresh = await fn()

    task = asyncio.ensure_future(set(key, fresh, redis, ttl))
    task.add_done_callback(
        lambda t: (
            logger.warning("Cache set failed: %s", t.exception())
            if t.exception()
            else None
        )
    )

    return {"data": fresh, "from_cache": False}
