from redis.asyncio import Redis

from app.core.config import settings

redis_client: Redis | None = None


async def get_redis() -> Redis:
    if redis_client is None:
        raise RuntimeError("Redis is not connected")
    return redis_client


async def connect_redis() -> None:
    global redis_client
    redis_client = Redis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
    )


async def disconnect_redis() -> None:
    if redis_client:
        await redis_client.aclose()
