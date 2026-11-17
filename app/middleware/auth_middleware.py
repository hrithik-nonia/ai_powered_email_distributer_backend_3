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
from typing import Callable


logger = logging.getLogger(__name__)
bearer_scheme = HTTPBearer(auto_error=False)


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )

# get current_user function is used to retrieve the current authenticated user based on the provided bearer token. It checks the validity of the token, verifies it, and retrieves the user information from either Redis cache or MongoDB. If the token is invalid, expired, or revoked, it raises an HTTP 401 Unauthorized exception.
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


# require_role function is a dependency that checks if the current authenticated user has one of the specified roles. It retrieves the current user using the get_current_user function and verifies their role. If the user's role does not match any of the required roles, it raises an HTTP 403 Forbidden exception.
def require_role(*roles: str) -> Callable:
    async def dependency(
        current_user: dict = Depends(get_current_user),
    ) -> dict:
        user_role = current_user.get("role")
        if user_role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {', '.join(roles)}",
            )
        return current_user
    return dependency