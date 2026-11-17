import os
import uuid
from datetime import datetime, timezone, timedelta

from jose import JWTError, ExpiredSignatureError, jwt
import bcrypt

JWT_SECRET = os.getenv("JWT_SECRET", "changeme")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))


class ExpiredTokenError(Exception):
    pass


class TokenVerificationError(Exception):
    pass


class AuthenticationHelper:

    # Password hashing and verification
    @staticmethod
    def hash_password(password: str) -> str:
        # 72 byte limit ke liye truncate karo
        password_bytes = password.encode("utf-8")[:72]
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password_bytes, salt).decode("utf-8")

    # Password verification
    @staticmethod
    def verify_password(plain: str, hashed: str) -> bool:
        plain_bytes = plain.encode("utf-8")[:72]
        hashed_bytes = hashed.encode("utf-8")
        return bcrypt.checkpw(plain_bytes, hashed_bytes)

    # Token creation and verification
    @staticmethod
    def create_access_token(user_id: str, email: str, role: str) -> str:
        expires = datetime.now(timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
        payload = {
            "user_id": user_id,
            "email": email,
            "role": role,
            "jti": str(uuid.uuid4()),
            "exp": expires,
            "type": "access",
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    @staticmethod
    def create_refresh_token(
        user_id: str, email: str, role: str
    ) -> tuple[str, str, datetime]:
        jti = str(uuid.uuid4())
        expires = datetime.now(timezone.utc) + timedelta(
            days=REFRESH_TOKEN_EXPIRE_DAYS
        )
        payload = {
            "user_id": user_id,
            "email": email,
            "role": role,
            "jti": jti,
            "exp": expires,
            "type": "refresh",
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        return token, jti, expires

    @staticmethod
    def verify_access_token(token: str) -> dict:
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            if payload.get("type") != "access":
                raise TokenVerificationError("Invalid token type")
            return payload
        except ExpiredSignatureError:
            raise ExpiredTokenError("Access token expired")
        except JWTError:
            raise TokenVerificationError("Invalid access token")

    @staticmethod
    def verify_refresh_token(token: str) -> dict:
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            if payload.get("type") != "refresh":
                raise TokenVerificationError("Invalid token type")
            return payload
        except ExpiredSignatureError:
            raise ExpiredTokenError("Refresh token expired")
        except JWTError:
            raise TokenVerificationError("Invalid refresh token")
        
        
    @staticmethod
    def get_jti_from_token(token: str) -> str | None:
        try:
            payload = jwt.decode(
                token, JWT_SECRET,
                algorithms=[JWT_ALGORITHM],
                options={"verify_exp": False}
            )
            return payload.get("jti")
        except Exception:
            return None