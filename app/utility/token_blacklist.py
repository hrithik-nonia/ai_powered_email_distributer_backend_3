from datetime import datetime, timezone
from app.redis import redis_client

PREFIX = "blacklist:"


class AccessTokenBlacklist:

    @staticmethod
    def _key(jti: str) -> str:
        return f"{PREFIX}{jti}"

    @classmethod
    async def blacklist(cls, jti: str, expires_at: datetime) -> None:
        ttl = int((expires_at - datetime.now(timezone.utc)).total_seconds())
        if ttl > 0:
            await redis_client.setex(cls._key(jti), ttl, "1")

    @classmethod
    async def is_revoked(cls, jti: str) -> bool:
        result = await redis_client.exists(cls._key(jti))
        return bool(result)