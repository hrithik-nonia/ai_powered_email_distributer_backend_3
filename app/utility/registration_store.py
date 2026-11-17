import json
from datetime import datetime
from typing import Any
from app.redis import redis_client

TTL = 300
PREFIX = "pending_registration:"


class RegistrationStore:

    @staticmethod
    def _key(email: str) -> str:
        return f"{PREFIX}{email}"

    @classmethod
    async def create(cls, data: dict[str, Any]) -> bool:
        def serialize(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            return str(obj)
        created = await redis_client.set(
            cls._key(data["email"]),
            json.dumps(data, default=serialize),
            ex=TTL,
            nx=True,
        )
        return bool(created)

    @classmethod
    async def get_and_delete(cls, email: str) -> dict[str, Any] | None:
        raw = await redis_client.getdel(cls._key(email))
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return None

    @classmethod
    async def get(cls, email: str) -> dict[str, Any] | None:
        raw = await redis_client.get(cls._key(email))
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return None

    @classmethod
    async def restore(cls, email: str, data: dict[str, Any], ttl: int) -> None:
        if ttl <= 0:
            await redis_client.delete(cls._key(email))
            return
        def serialize(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            return str(obj)
        await redis_client.set(
            cls._key(email),
            json.dumps(data, default=serialize),
            ex=ttl,
        )

    @classmethod
    async def delete(cls, email: str) -> None:
        await redis_client.delete(cls._key(email))