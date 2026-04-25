from pydantic import BaseModel
from typing import Optional, Literal


TLCTransactionType = Literal["earned", "redeemed_tokens", "redeemed_trust", "platform_fee"]
RedeemType = Literal["tokens", "trust", "cashout"]


class TLCWallet(BaseModel):
    user_id: str
    tlc_balance: float
    total_earned: float
    total_redeemed: float
    updated_at: str


class TLCTransaction(BaseModel):
    id: str
    user_id: str
    type: TLCTransactionType
    amount: float
    loan_id: Optional[str]    # which loan triggered this (None for redemptions)
    description: str
    created_at: str


class RedeemRequest(BaseModel):
    type: RedeemType
    tlc_amount: float
    agent_id: Optional[str] = None  # required for type='trust'


class RedeemResponse(BaseModel):
    success: bool
    tlc_spent: float
    value_received: str          # human-readable: "150 Groq tokens" / "+0.03 trust" / "coming soon"
    new_tlc_balance: float
    description: str
