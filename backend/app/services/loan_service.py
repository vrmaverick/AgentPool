import uuid
from datetime import datetime, timedelta
from app.db import queries
from app.core import decision_agent
from app.config import (
    MIN_TRUST_TO_BORROW, MIN_TRUST_TO_LEND, LENDER_YIELD_PCT, 
    PLATFORM_FEE_PCT, PROXY_TOKEN_TTL_MINUTES
)

async def find_lender_candidates(borrower_agent_id: str, borrower_user_id: str, amount: float) -> list[dict]:
    all_agents = await queries.get_all_agents()
    
    candidates = []
    for agent in all_agents:
        if agent["role"] == "lender" and \
           agent["trust_score"] >= MIN_TRUST_TO_LEND and \
           agent["token_balance"] >= amount and \
           agent["user_id"] != borrower_user_id:
               
            max_bal = agent.get("max_balance", agent["token_balance"] or 1)
            score = (agent["token_balance"] / max_bal if max_bal > 0 else 0) * 0.6 + agent["trust_score"] * 0.4
            candidates.append((score, agent))
            
    candidates.sort(key=lambda x: x[0], reverse=True)
    return [c[1] for c in candidates[:3]]

async def request_loan(borrower_agent_id: str, requesting_user_id: str, amount: float) -> dict:
    borrower = await queries.get_agent_by_id(borrower_agent_id)
    if not borrower or borrower["user_id"] != requesting_user_id:
        return {"approved": False, "reason": "Borrower agent not found or unauthorized.", "status": 404}
    
    if borrower["trust_score"] < MIN_TRUST_TO_BORROW:
        return {"approved": False, "reason": f"Trust score {borrower['trust_score']} too low to borrow. Need {MIN_TRUST_TO_BORROW}.", "status": 400}
        
    candidates = await find_lender_candidates(borrower_agent_id, requesting_user_id, amount)
    if not candidates:
        return {"approved": False, "reason": "No lender candidates available.", "status": 404}
        
    borrower_data = {**borrower, "requested_amount": amount}
    
    def strip_keys(ag):
        return {k: v for k, v in ag.items() if k not in ["encrypted_api_key"]}
        
    decision = await decision_agent.evaluate_loan_request(
        borrower=strip_keys(borrower_data),
        candidates=[strip_keys(c) for c in candidates]
    )
    
    if decision.get("approve"):
        lender_id = decision.get("lender_id")
        lender = next((c for c in candidates if c["id"] == lender_id), None)
        if not lender:
            lender = candidates[0]
            lender_id = lender["id"]
            
        tlc_yield = amount * LENDER_YIELD_PCT
        platform_tlc = amount * PLATFORM_FEE_PCT
        
        # Deduct from lender, add to borrower
        await queries.update_agent_token_balance(lender_id, -amount)
        await queries.update_agent_token_balance(borrower_agent_id, amount)
        
        due_time = (datetime.utcnow() + timedelta(days=7)).isoformat() + "Z"
        
        loan = await queries.create_loan(
            lender_agent_id=lender_id,
            borrower_agent_id=borrower_agent_id,
            lender_user_id=lender["user_id"],
            borrower_user_id=borrower["user_id"],
            amount=amount,
            tlc_yield_amount=tlc_yield,
            platform_tlc_fee=platform_tlc,
            due_time=due_time
        )
        
        ptk_id = f"ptk_{uuid.uuid4().hex}"
        expires_at = (datetime.utcnow() + timedelta(minutes=PROXY_TOKEN_TTL_MINUTES)).isoformat() + "Z"
        
        await queries.create_proxy_token(
            token_id=ptk_id,
            agent_id=lender_id,
            user_id=requesting_user_id,
            credits_remaining=amount,
            expires_at=expires_at,
            key_source="lender",
            loan_id=loan["id"],
            lender_user_id=lender["user_id"]
        )
        
        await queries.insert_tx_log(
            event_type="loan_created",
            actor_user_id=requesting_user_id,
            related_id=loan["id"],
            description=f"Loan of {amount} tokens from {lender['name']} to {borrower['name']}"
        )
        
        return {
            "approved": True,
            "loan_id": loan["id"],
            "ptk": ptk_id,
            "lender_name": lender["name"],
            "amount": amount,
            "tlc_yield_pending": tlc_yield,
            "due_time": due_time,
            "reason": decision.get("reason", "Approved by Decision Agent")
        }
    else:
        return {"approved": False, "reason": decision.get("reason", "Denied by Decision Agent"), "status": 400}

async def repay_loan(loan_id: str, repaying_user_id: str) -> dict:
    from app.core import tlc_engine
    from app.config import PLATFORM_USER_ID
    
    loan = await queries.get_loan_by_id(loan_id)
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found.")
        
    if loan["status"] != "active":
        raise HTTPException(status_code=400, detail="Loan is not active.")
        
    if loan["borrower_user_id"] != repaying_user_id:
        raise HTTPException(status_code=403, detail="Only the borrower can repay the loan.")
        
    borrower_agent = await queries.get_agent_by_id(loan["borrower_agent_id"])
    if not borrower_agent or borrower_agent.get("token_balance", 0) < loan["amount"]:
        raise HTTPException(status_code=400, detail="Insufficient tokens to repay the loan. Need to accumulate more tokens.")
        
    # Deduct loan.amount from borrower token_balance
    await queries.update_agent_token_balance(loan["borrower_agent_id"], -loan["amount"])
    
    # Add loan.amount to lender token_balance
    await queries.update_agent_token_balance(loan["lender_agent_id"], loan["amount"])
    
    # Mark loan status = "repaid"
    now_str = datetime.utcnow().isoformat() + "Z"
    await queries.update_loan_status(loan_id, "repaid", now_str)
    
    # Expire proxy_token
    await queries.expire_proxy_tokens_by_loan_id(loan_id)
    
    # Mint TLC
    await tlc_engine.mint_tlc(
        user_id=loan["lender_user_id"],
        amount=loan["tlc_yield_amount"],
        type="earned",
        loan_id=loan_id,
        description=f"Yield from lending {loan['amount']} tokens"
    )
    
    await tlc_engine.mint_tlc(
        user_id=PLATFORM_USER_ID,
        amount=loan["platform_tlc_fee"],
        type="platform_fee",
        loan_id=loan_id,
        description="Platform fee"
    )
    
    # Update trust scores
    due_time_dt = datetime.fromisoformat(loan["due_time"].rstrip("Z"))
    on_time = datetime.utcnow() <= due_time_dt
    
    from app.services import agent_service
    if on_time:
        borrower_trust_new = await agent_service.update_trust_score(loan["borrower_agent_id"], 0.02)
        lender_trust_new = await agent_service.update_trust_score(loan["lender_agent_id"], 0.005)
    else:
        borrower_trust_new = await agent_service.update_trust_score(loan["borrower_agent_id"], -0.05)
        lender_trust_new = borrower_agent.get("trust_score", 0.8) # lender untouched on late payment? Prompt says borrower -0.05
    
    await queries.insert_tx_log(
        event_type="loan_repaid",
        actor_user_id=repaying_user_id,
        related_id=loan_id,
        description=f"Loan {loan_id} repaid {'on time' if on_time else 'late'}."
    )
    
    return {
        "repaid": True,
        "borrower_tokens_returned": loan["amount"],
        "lender_tokens_restored": loan["amount"],
        "lender_tlc_earned": loan["tlc_yield_amount"],
        "platform_tlc_fee": loan["platform_tlc_fee"],
        "on_time": on_time,
        "borrower_trust_new": borrower_trust_new,
        "lender_trust_new": lender_trust_new
    }
