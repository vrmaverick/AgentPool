"""
users.py — /user/register and /user/login endpoints.
"""

from fastapi import APIRouter, status
from pydantic import BaseModel, EmailStr
from typing import Optional

from app.services.user_service import register_user, login_user

router = APIRouter()


class RegisterBody(BaseModel):
    name: str
    email: EmailStr
    password: str
    city: Optional[str] = None
    timezone: Optional[str] = None


class LoginBody(BaseModel):
    email: EmailStr
    password: str


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(body: RegisterBody):
    user_id = await register_user(
        name=body.name,
        email=body.email,
        password=body.password,
        city=body.city,
        timezone=body.timezone,
    )
    return {"user_id": user_id, "message": "Registered successfully"}


@router.post("/login")
async def login(body: LoginBody):
    result = await login_user(email=body.email, password=body.password)
    return {
        "access_token": result["access_token"],
        "token_type": "bearer",
        "user_id": result["user_id"],
    }
