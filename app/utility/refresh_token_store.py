import json
from datetime import datetime
from app.redis import redis_client

PREFIX = "refresh:"


class RefreshTokenStore:

    @staticmethod
    def _key(user_id: str, jti: str) -> str:
        return f"{PREFIX}{user_id}:{jti}"

    @classmethod
    async def create_session(
        cls,
        user_id: str,
        jti: str,
        token: str,
        expires_at: datetime,
    ) -> None:
        from datetime import timezone
        ttl = int((expires_at - datetime.now(timezone.utc)).total_seconds())
        if ttl > 0:
            await redis_client.setex(
                cls._key(user_id, jti),
                ttl,
                json.dumps({"token": token}),
            )

    @classmethod
    async def rotate(
        cls,
        user_id: str,
        old_jti: str,
        old_token: str,
        new_jti: str,
        new_token: str,
        new_expires_at: datetime,
    ) -> bool:
        exists = await redis_client.exists(cls._key(user_id, old_jti))
        if not exists:
            return False
        await redis_client.delete(cls._key(user_id, old_jti))
        await cls.create_session(user_id, new_jti, new_token, new_expires_at)
        return True

    @classmethod
    async def revoke(cls, user_id: str, jti: str) -> None:
        await redis_client.delete(cls._key(user_id, jti))