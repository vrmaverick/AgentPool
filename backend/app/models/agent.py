from pydantic import BaseModel
from typing import Optional


class AgentCreate(BaseModel):
    user_id: str
    name: str
    role: str
    api_key: str          # plaintext — encrypted in service layer, never stored raw
    max_balance: float
    location: Optional[str] = None
    timezone: Optional[str] = None
    preferred_start_hour: Optional[int] = None   # 0-23 local hour (idle window start)
    preferred_end_hour: Optional[int] = None     # 0-23 local hour (idle window end)


class AgentResponse(BaseModel):
    id: str
    user_id: str
    name: str
    role: str
    api_key_masked: str   # "gsk_ab...xxxx" — NEVER encrypted_api_key
    token_balance: float
    max_balance: float
    trust_score: float
    loans_taken: int
    loans_given: int
    repayments_ok: int
    usage_rate: float
    last_active: Optional[str]
    created_at: str
    location: Optional[str]
    timezone: Optional[str]
    preferred_start_hour: Optional[int]
    preferred_end_hour: Optional[int]
