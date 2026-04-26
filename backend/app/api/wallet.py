from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.middleware.auth import get_current_user
from app.db import queries
from app.core import tlc_engine

router = APIRouter()

class RedeemRequest(BaseModel):
    type: str
    tlc_amount: float
    agent_id: Optional[str] = None

@router.get("/")
async def get_wallet(current_user_id: str = Depends(get_current_user)):
    wallet = await queries.get_tlc_wallet(current_user_id)
    if not wallet:
        wallet = {
            "tlc_balance": 0.0,
            "total_earned": 0.0,
            "total_redeemed": 0.0,
        }
        
    history = await queries.get_tlc_history(current_user_id, limit=20)
    
    # Compute active loans as lender
    all_loans = await queries.get_loans_by_user(current_user_id)
    active_loans_as_lender = [l for l in all_loans if l["status"] == "active" and l["lender_user_id"] == current_user_id]
    
    pending_tlc = sum(l.get("tlc_yield_amount", 0) for l in active_loans_as_lender)
    
    return {
        "tlc_balance": wallet.get("tlc_balance", 0.0),
        "total_earned": wallet.get("total_earned", 0.0),
        "total_redeemed": wallet.get("total_redeemed", 0.0),
        "pending_tlc": pending_tlc,
        "redemption_options": [
            {"type": "tokens", "rate": "1 TLC = 1 Groq token", "min": 10},
            {"type": "trust", "rate": "50 TLC = +0.05 trust", "min": 50},
            {"type": "cashout", "rate": "1000 TLC = ₹1 (coming soon)", "min": 1000, "disabled": True}
        ],
        "history": [
            {
                "date": tx.get("created_at"),
                "type": tx.get("type"),
                "amount": tx.get("amount"),
                "description": tx.get("description"),
                "loan_id": tx.get("loan_id")
            }
            for tx in history
        ]
    }

@router.post("/redeem")
async def redeem_tlc(req: RedeemRequest, current_user_id: str = Depends(get_current_user)):
    if req.type == "cashout":
        raise HTTPException(status_code=400, detail="Coming soon. Accumulate TLC now.")
        
    if req.type not in ["tokens", "trust"]:
        raise HTTPException(status_code=400, detail="Invalid redemption type.")
        
    if not req.agent_id:
        raise HTTPException(status_code=400, detail="agent_id is required for this redemption type.")
        
    agent = await queries.get_agent_by_id(req.agent_id)
    if not agent or agent["user_id"] != current_user_id:
        raise HTTPException(status_code=403, detail="Not authorized to redeem to this agent.")

    if req.type == "tokens":
        if req.tlc_amount < 10:
            raise HTTPException(status_code=400, detail="Minimum 10 TLC required for tokens.")
        result = await tlc_engine.redeem_for_tokens(current_user_id, req.tlc_amount, req.agent_id)
        
    elif req.type == "trust":
        if req.tlc_amount < 50:
            raise HTTPException(status_code=400, detail="Minimum 50 TLC required for trust.")
        result = await tlc_engine.redeem_for_trust(current_user_id, req.tlc_amount, req.agent_id)
        
    return result
