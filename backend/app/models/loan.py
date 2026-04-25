from pydantic import BaseModel
from typing import Optional


class LoanCreate(BaseModel):
    lender_agent_id: str
    borrower_agent_id: str
    amount: float


class LoanResponse(BaseModel):
    id: str
    lender_agent_id: str
    borrower_agent_id: str
    lender_user_id: str
    borrower_user_id: str
    amount: float
    tlc_yield_amount: float   # amount * LENDER_YIELD_PCT — minted on repayment
    platform_tlc_fee: float   # amount * PLATFORM_FEE_PCT — minted on repayment
    status: str               # 'active' | 'repaid' | 'defaulted'
    start_time: str
    due_time: str
    repaid_at: Optional[str]
