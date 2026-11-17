from datetime import datetime
from typing import Literal
from pydantic import BaseModel, EmailStr, field_validator


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: Literal["assistant", "client"]
    linked_assistant_id: str | None = None

    @field_validator("name")
    @classmethod
    def name_valid(cls, v):
        if len(v.strip()) < 2:
            raise ValueError("Name must be at least 2 characters")
        return v.strip()

    @field_validator("password")
    @classmethod
    def password_valid(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

    @field_validator("linked_assistant_id")
    @classmethod
    def client_needs_assistant(cls, v, info):
        if info.data.get("role") == "client" and not v:
            raise ValueError("linked_assistant_id is required for client role")
        return v


class OTPVerification(BaseModel):
    email: EmailStr
    otp: str

    @field_validator("otp")
    @classmethod
    def otp_valid(cls, v):
        if not v.isdigit() or len(v) != 6:
            raise ValueError("OTP must be 6 digits")
        return v


class ResendOTP(BaseModel):
    email: EmailStr


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    linked_assistant_id: str | None
    created_at: datetime


class OTPResponse(BaseModel):
    message: str
    email: str
    expires_in: int


class RegistrationResponse(BaseModel):
    message: str
    user: UserResponse


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"