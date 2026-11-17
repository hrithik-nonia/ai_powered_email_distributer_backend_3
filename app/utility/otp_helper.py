import os
import random
import string
from datetime import datetime, timezone, timedelta
import bcrypt
from passlib.context import CryptContext

OTP_EXPIRY_MINUTES = int(os.getenv("OTP_EXPIRY_MINUTES", "5"))
otp_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class OTPHelper:
    EXPIRY_MINUTES = OTP_EXPIRY_MINUTES
    MAX_ATTEMPTS = 5

    @staticmethod
    def generate_otp() -> str:
        return "".join(random.choices(string.digits, k=6))

    @staticmethod
    def hash_otp(otp: str) -> str:
        otp_bytes = otp.encode("utf-8")
        return bcrypt.hashpw(otp_bytes, bcrypt.gensalt()).decode("utf-8")

    @staticmethod
    def verify_otp(otp: str, hashed: str) -> bool:
        return bcrypt.checkpw(
            otp.encode("utf-8"),
            hashed.encode("utf-8")
        )

    @staticmethod
    def calculate_expiry() -> datetime:
        return datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRY_MINUTES)

    @staticmethod
    def is_expired(expires_at: datetime) -> bool:
        return datetime.now(timezone.utc) > expires_at