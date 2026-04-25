"""
user_service.py — Registration, login, profile retrieval.
"""

from zoneinfo import available_timezones
from fastapi import HTTPException, status
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta

from app.config import JWT_SECRET
from app.db.queries import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    upsert_tlc_wallet,
)

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
_ALGORITHM = "HS256"
_TOKEN_EXPIRE_HOURS = 24

_VALID_TIMEZONES = available_timezones()  # loaded once at import


def _validate_timezone(tz: str | None) -> None:
    if tz is not None and tz not in _VALID_TIMEZONES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid timezone '{tz}'. Must be a valid IANA timezone string.",
        )


async def register_user(
    name: str,
    email: str,
    password: str,
    city: str | None = None,
    timezone: str | None = None,
) -> str:
    """Hash password, persist user + TLC wallet. Returns user_id."""
    _validate_timezone(timezone)

    existing = await get_user_by_email(email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered.",
        )

    hashed_password = _pwd.hash(password)
    user = await create_user(
        name=name,
        email=email,
        hashed_password=hashed_password,
        city=city,
        timezone=timezone,
    )

    # Create TLC wallet for new user (balance starts at 0)
    await upsert_tlc_wallet(user["id"], tlc_delta=0, earned_delta=0, redeemed_delta=0)

    return user["id"]


async def login_user(email: str, password: str) -> dict:
    """Verify credentials, return JWT access token."""
    user = await get_user_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not _pwd.verify(password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    expire = datetime.utcnow() + timedelta(hours=_TOKEN_EXPIRE_HOURS)
    token = jwt.encode(
        {"sub": user["id"], "exp": expire},
        JWT_SECRET,
        algorithm=_ALGORITHM,
    )

    return {"access_token": token, "user_id": user["id"]}


async def get_user(user_id: str) -> dict:
    """Return user doc with hashed_password stripped."""
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    user.pop("hashed_password", None)
    return user
