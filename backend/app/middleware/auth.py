"""
auth.py — Two independent auth flows.

  1. JWT (Bearer token)  — use Depends(get_current_user) on any protected route
  2. Proxy token (ptk_)  — ONLY for POST /proxy/chat via validate_proxy_token()

NEVER mix them.
"""

from datetime import datetime
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

from app.config import JWT_SECRET
from app.db.queries import get_proxy_token

_ALGORITHM = "HS256"

# HTTPBearer renders a padlock + "Value" paste box in Swagger UI
_bearer = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> str:
    """
    FastAPI dependency — decode JWT, return user_id.
    Use as:  user_id: str = Depends(get_current_user)
    Raises HTTP 401 if token is missing, invalid, or expired.
    """
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[_ALGORITHM])
        user_id: str | None = payload.get("sub")
        if not user_id:
            raise ValueError("Missing sub claim")
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id


async def validate_proxy_token(ptk: str) -> dict:
    """
    Validate a proxy token (ptk_xxx) from Firestore.
    Raises HTTP 401 if not found or expired.
    Returns the full proxy_token dict on success.
    """
    record = await get_proxy_token(ptk)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid proxy token.",
        )

    expires_at = record.get("expires_at", "")
    try:
        exp_dt = datetime.fromisoformat(expires_at.rstrip("Z"))
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Proxy token has malformed expiry.",
        )

    if datetime.utcnow() > exp_dt:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Proxy token has expired.",
        )

    return record
