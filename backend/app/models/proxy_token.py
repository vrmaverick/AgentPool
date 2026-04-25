from pydantic import BaseModel
from typing import Optional


class ProxyTokenCreate(BaseModel):
    agent_id: str
    user_id: str
    credits_remaining: float


class ProxyToken(BaseModel):
    id: str              # the "ptk_xxx" bearer token value
    agent_id: str
    user_id: str
    credits_remaining: float
    created_at: str
    expires_at: str
