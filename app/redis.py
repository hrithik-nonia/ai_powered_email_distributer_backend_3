import os
import logging
import redis.asyncio as aioredis
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

redis_client: aioredis.Redis = aioredis.from_url(
    REDIS_URL,
    encoding="utf-8",
    decode_responses=True,
)


async def ping_redis() -> bool:
    try:
        await redis_client.ping()
        logger.info("Redis connected successfully")
        return True
    except Exception as exc:
        logger.warning("Redis connection failed: %s", exc)
        return False


async def close_redis() -> None:
    await redis_client.aclose()
    logger.info("Redis connection closed")