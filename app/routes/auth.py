import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException, Request, Response, status
from pymongo.errors import DuplicateKeyError

from app.database import users_collection
from app.middleware.auth_middleware import get_current_user
from app.models.user import (
    LoginResponse, OTPResponse, OTPVerification,
    RegistrationResponse, ResendOTP, TokenResponse,
    UserCreate, UserResponse,UserLogin
)
from app.redis import redis_client
from app.utility.auth_cookie import AuthCookie
from app.utility.authentication_helper import (
    ACCESS_TOKEN_EXPIRE_MINUTES, AuthenticationHelper, ExpiredTokenError, TokenVerificationError,
)
from app.utility.otp_helper import OTPHelper
from app.utility.registration_store import RegistrationStore
from app.utility.refresh_token_store import RefreshTokenStore
from app.utility.token_blacklist import AccessTokenBlacklist
from app.utility.email_helper import EmailHelper
from fastapi import Depends

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


def serialize_user(user: dict) -> UserResponse:
    return UserResponse(
        id=str(user["_id"]),
        name=user["name"],
        email=user["email"],
        role=user["role"],
        linked_assistant_id=user.get("linked_assistant_id"),
        created_at=user["created_at"],
    )


def _unauthorized(detail: str):
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


# ─── Register ───
@router.post("/register", response_model=OTPResponse)
async def register(payload: UserCreate):
    existing = await users_collection.find_one({"email": payload.email})
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    pending = await RegistrationStore.get(payload.email)
    if pending:
        raise HTTPException(
            status_code=409,
            detail="OTP already sent. Please verify or wait for it to expire.",
        )

    otp = OTPHelper.generate_otp()
    expires_at = OTPHelper.calculate_expiry()
    now = datetime.now(timezone.utc)

    document = {
        "name": payload.name,
        "email": payload.email,
        "password_hash": await asyncio.to_thread(
            AuthenticationHelper.hash_password, payload.password
        ),
        "role": payload.role,
        "linked_assistant_id": payload.linked_assistant_id,
        "otp_hash": await asyncio.to_thread(OTPHelper.hash_otp, otp),
        "otp_attempts": 0,
        "created_at": now.isoformat(),
        "expires_at": expires_at.isoformat(),
    }

    created = await RegistrationStore.create(document)
    if not created:
        raise HTTPException(status_code=409, detail="OTP already sent.")

    await EmailHelper.send_otp_email(payload.email, otp)

    return OTPResponse(
        message="OTP sent. Please check your email.",
        email=payload.email,
        expires_in=OTPHelper.EXPIRY_MINUTES * 60,
    )


# ─── Verify OTP ───
@router.post("/verify-otp", response_model=RegistrationResponse)
async def verify_otp(payload: OTPVerification):
    pending = await RegistrationStore.get_and_delete(payload.email)
    if pending is None:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    otp_hash = pending.get("otp_hash")
    if not otp_hash:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    expires_at = datetime.fromisoformat(pending["expires_at"])
    if OTPHelper.is_expired(expires_at):
        raise HTTPException(status_code=400, detail="OTP expired. Please register again.")

    attempts = int(pending.get("otp_attempts") or 0)
    if attempts >= OTPHelper.MAX_ATTEMPTS:
        raise HTTPException(status_code=400, detail="Too many attempts. Please register again.")

    otp_valid = await asyncio.to_thread(OTPHelper.verify_otp, payload.otp, otp_hash)

    if not otp_valid:
        attempts += 1
        if attempts >= OTPHelper.MAX_ATTEMPTS:
            raise HTTPException(status_code=400, detail="Too many attempts. Please register again.")
        from datetime import timezone as tz
        remaining = max(1, int((expires_at - datetime.now(tz.utc)).total_seconds()))
        pending["otp_attempts"] = attempts
        await RegistrationStore.restore(payload.email, pending, remaining)
        raise HTTPException(
            status_code=400,
            detail=f"Incorrect OTP. {OTPHelper.MAX_ATTEMPTS - attempts} attempts remaining.",
        )

    existing = await users_collection.find_one({"email": pending["email"]})
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    user_document = {
        "name": pending["name"],
        "email": pending["email"],
        "password_hash": pending["password_hash"],
        "role": pending["role"],
        "linked_assistant_id": pending.get("linked_assistant_id"),
        "created_at": datetime.now(timezone.utc),
    }

    try:
        result = await users_collection.insert_one(user_document)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="Email already registered")
    except Exception:
        from datetime import timezone as tz
        remaining = max(1, int((expires_at - datetime.now(tz.utc)).total_seconds()))
        await RegistrationStore.restore(payload.email, pending, remaining)
        raise HTTPException(status_code=500, detail="Registration failed. Please try again.")

    user = {"_id": result.inserted_id, **user_document}
    return RegistrationResponse(
        message="Registration successful. Please log in.",
        user=serialize_user(user),
    )


# ─── Resend OTP ───
@router.post("/resend-otp", response_model=OTPResponse)
async def resend_otp(payload: ResendOTP):
    pending = await RegistrationStore.get(payload.email)
    if pending is None:
        raise HTTPException(status_code=400, detail="No pending registration found.")

    otp = OTPHelper.generate_otp()
    expires_at = OTPHelper.calculate_expiry()
    pending["otp_hash"] = await asyncio.to_thread(OTPHelper.hash_otp, otp)
    pending["otp_attempts"] = 0
    pending["expires_at"] = expires_at.isoformat()

    await RegistrationStore.restore(payload.email, pending, 300)
    await EmailHelper.send_otp_email(payload.email, otp)

    return OTPResponse(
        message="New OTP sent.",
        email=payload.email,
        expires_in=OTPHelper.EXPIRY_MINUTES * 60,
    )


# ─── Login ───
@router.post("/login", response_model=LoginResponse)
async def login(payload: UserLogin, response: Response):
    cached = await redis_client.get(f"user:{payload.email}")
    if cached:
        user = json.loads(cached)
        user["_id"] = user.get("_id") or user.get("id")
    else:
        user = await users_collection.find_one({"email": payload.email})
        if user is None:
            raise HTTPException(status_code=401, detail="Invalid email or password")

    password_hash = user.get("password_hash")
    if not password_hash:
        user_db = await users_collection.find_one({"email": payload.email})
        if user_db is None:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        password_hash = user_db["password_hash"]
        user = user_db

    valid = await asyncio.to_thread(
        AuthenticationHelper.verify_password, payload.password, password_hash
    )
    if not valid:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # ── Role check ──────────────────────────────────────────────
    if payload.role and user["role"] != payload.role:
        raise HTTPException(
            status_code=403,
            detail=f"This account is registered as '{user['role']}'. Please login with the correct role."
        )
    # ────────────────────────────────────────────────────────────

    user_id = str(user.get("_id") or user.get("id"))
    access_token = AuthenticationHelper.create_access_token(
        user_id=user_id, email=user["email"], role=user["role"]
    )
    refresh_token, jti, refresh_expires = AuthenticationHelper.create_refresh_token(
        user_id=user_id, email=user["email"], role=user["role"]
    )

    # store access token for revocation check
    access_jti = AuthenticationHelper.get_jti_from_token(access_token)
    if access_jti:
        await redis_client.setex(
            f"active_access:{user_id}",
            ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            access_jti,
        )

    await RefreshTokenStore.create_session(user_id, jti, refresh_token, refresh_expires)

    user_to_cache = {k: v for k, v in user.items() if k != "password_hash"}
    await redis_client.setex(
        f"user:{payload.email}", 600, json.dumps(user_to_cache, default=str)
    )

    AuthCookie.set(response, refresh_token)

    user_response = UserResponse(
        id=user_id,
        name=user["name"],
        email=user["email"],
        role=user["role"],
        linked_assistant_id=user.get("linked_assistant_id"),
        created_at=user.get("created_at", datetime.now(timezone.utc)),
    )
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_response,
    )

# ─── Refresh ───
@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: Request, response: Response):
    refresh_token = request.cookies.get(AuthCookie.NAME)
    if not refresh_token:
        raise _unauthorized("Refresh token missing")

    try:
        payload = AuthenticationHelper.verify_refresh_token(refresh_token)
    except ExpiredTokenError:
        raise _unauthorized("Refresh token expired")
    except TokenVerificationError:
        raise _unauthorized("Invalid refresh token")

    user_id = payload.get("user_id")
    jti = payload.get("jti")
    email = payload.get("email")

    try:
        object_id = ObjectId(user_id)
    except (InvalidId, TypeError):
        raise _unauthorized("Invalid token payload")

    user = await users_collection.find_one({"_id": object_id})
    if user is None:
        raise _unauthorized("User not found")

    # ─── Old access token Redis se lo aur blacklist karo ───
    old_jti = await redis_client.get(f"active_access:{user_id}")
    if old_jti:
        old_exp = datetime.now(timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
        await AccessTokenBlacklist.blacklist(old_jti, old_exp)
        await redis_client.delete(f"active_access:{user_id}")

    # ─── Naye tokens banao ───
    new_access = AuthenticationHelper.create_access_token(
        user_id=str(user["_id"]),
        email=user["email"],
        role=user["role"],
    )
    new_refresh, new_jti, new_expires = AuthenticationHelper.create_refresh_token(
        user_id=str(user["_id"]),
        email=user["email"],
        role=user["role"],
    )

    # ─── Refresh token rotate karo ───
    rotated = await RefreshTokenStore.rotate(
        user_id=str(user["_id"]),
        old_jti=jti,
        old_token=refresh_token,
        new_jti=new_jti,
        new_token=new_refresh,
        new_expires_at=new_expires,
    )
    if not rotated:
        raise _unauthorized("Refresh token revoked")

    # ─── Naya JTI Redis mein save karo ───
    new_access_jti = AuthenticationHelper.get_jti_from_token(new_access)
    if new_access_jti:
        await redis_client.setex(
            f"active_access:{user_id}",
            ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            new_access_jti,
        )

    # ─── Redis user cache update karo ───
    user_to_cache = {k: v for k, v in user.items() if k != "password_hash"}
    await redis_client.setex(
        f"user:{email}", 600, json.dumps(user_to_cache, default=str)
    )

    AuthCookie.set(response, new_refresh)
    return TokenResponse(access_token=new_access, token_type="bearer")

# ─── Logout ───
@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    current_user: dict = Depends(get_current_user),
):
    refresh_token = request.cookies.get(AuthCookie.NAME)
    if refresh_token:
        try:
            payload = AuthenticationHelper.verify_refresh_token(refresh_token)
            jti = payload.get("jti")
            user_id = payload.get("user_id")
            if jti and user_id:
                await RefreshTokenStore.revoke(user_id, jti)
        except Exception:
            pass

    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        try:
            token = auth_header[7:]
            payload = AuthenticationHelper.verify_access_token(token)
            jti = payload.get("jti")
            exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
            if jti:
                await AccessTokenBlacklist.blacklist(jti, exp)
        except Exception:
            pass

    await redis_client.delete(f"user:{current_user.get('email')}")
    AuthCookie.clear(response)
    return {"message": "Logged out successfully"}


# ─── Me ───
@router.get("/me", response_model=UserResponse)
async def me(current_user: dict = Depends(get_current_user)):
    return UserResponse(
        id=str(current_user.get("_id") or current_user.get("id")),
        name=current_user["name"],
        email=current_user["email"],
        role=current_user["role"],
        linked_assistant_id=current_user.get("linked_assistant_id"),
        created_at=current_user.get("created_at", datetime.now(timezone.utc)),
    )