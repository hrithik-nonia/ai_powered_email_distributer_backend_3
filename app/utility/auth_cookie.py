import os
from fastapi import Response

IS_PRODUCTION = os.getenv("APP_ENV", "development") == "production"


class AuthCookie:
    NAME = "refresh_token"
    MAX_AGE = 7 * 24 * 60 * 60  # 7 days

    @classmethod
    def set(cls, response: Response, token: str) -> None:
        response.set_cookie(
            key=cls.NAME,
            value=token,
            httponly=True,
            secure=IS_PRODUCTION,
            samesite="lax",
            max_age=cls.MAX_AGE,
        )

    @classmethod
    def clear(cls, response: Response) -> None:
        response.delete_cookie(key=cls.NAME)