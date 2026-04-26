from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List

from app.middleware.auth import get_current_user
from app.services import loan_service
from app.db import queries

router = APIRouter()

class LoanRequest(BaseModel):
    borrower_agent_id: str
    amount: float

@router.post("/request")
async def request_loan(req: LoanRequest, current_user_id: str = Depends(get_current_user)):
    result = await loan_service.request_loan(req.borrower_agent_id, current_user_id, req.amount)
    if not result.get("approved"):
        status_code = result.get("status", 400)
        raise HTTPException(status_code=status_code, detail=result.get("reason"))
    return result

@router.get("/")
async def get_loans(current_user_id: str = Depends(get_current_user)):
    user_loans = await queries.get_loans_by_user(current_user_id)
    
    return {
        "active": [l for l in user_loans if l["status"] == "active"],
        "history": [l for l in user_loans if l["status"] != "active"],
        "my_active_as_lender": [l for l in user_loans if l["status"] == "active" and l["lender_user_id"] == current_user_id],
        "my_active_as_borrower": [l for l in user_loans if l["status"] == "active" and l["borrower_user_id"] == current_user_id]
    }

@router.post("/repay/{loan_id}")
async def repay_loan(loan_id: str, current_user_id: str = Depends(get_current_user)):
    return await loan_service.repay_loan(loan_id, current_user_id)
