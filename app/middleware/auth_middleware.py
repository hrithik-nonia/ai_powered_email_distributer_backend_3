import json
import logging
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.database import users_collection
from app.redis import redis_client
from app.utility.authentication_helper import (
    AuthenticationHelper,
    ExpiredTokenError,
    TokenVerificationError,
)
from app.utility.token_blacklist import AccessTokenBlacklist

logger = logging.getLogger(__name__)
bearer_scheme = HTTPBearer(auto_error=False)


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized("Not authenticated")

    try:
        payload = AuthenticationHelper.verify_access_token(credentials.credentials)
    except ExpiredTokenError:
        raise _unauthorized("Token has expired")
    except TokenVerificationError:
        raise _unauthorized("Could not validate credentials")

    jti = payload.get("jti")
    if jti and await AccessTokenBlacklist.is_revoked(jti):
        raise _unauthorized("Token has been revoked")

    user_id = payload.get("user_id")
    email = payload.get("email")
    if not user_id:
        raise _unauthorized("Invalid token payload")

    # Redis check
    if email:
        cached = await redis_client.get(f"user:{email}")
        if cached:
            return json.loads(cached)

    # MongoDB fallback
    try:
        object_id = ObjectId(user_id)
    except (InvalidId, TypeError):
        raise _unauthorized("Invalid user identifier")

    user = await users_collection.find_one({"_id": object_id})
    if user is None:
        raise _unauthorized("User not found")

    # Cache karo
    user_to_cache = {k: v for k, v in user.items() if k != "password_hash"}
    await redis_client.setex(
        f"user:{email}",
        600,
        json.dumps(user_to_cache, default=str),
    )

    return user