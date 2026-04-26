from fastapi import HTTPException
from app.db import queries
from app.services import agent_service
from app.config import TLC_TO_TOKEN_RATE, TLC_TO_TRUST_RATE

async def mint_tlc(user_id: str, amount: float, type: str, loan_id: str | None, description: str) -> float:
    await queries.upsert_tlc_wallet(user_id, tlc_delta=amount, earned_delta=amount)
    await queries.insert_tlc_transaction(
        user_id=user_id,
        type=type,
        amount=amount,
        loan_id=loan_id,
        description=description
    )
    
    wallet = await queries.get_tlc_wallet(user_id)
    return wallet.get("tlc_balance", 0.0) if wallet else 0.0

async def deduct_tlc(user_id: str, amount: float) -> float:
    wallet = await queries.get_tlc_wallet(user_id)
    if not wallet or wallet.get("tlc_balance", 0.0) < amount:
        raise HTTPException(status_code=400, detail="Insufficient TLC balance.")
        
    await queries.upsert_tlc_wallet(user_id, tlc_delta=-amount, redeemed_delta=amount)
    
    wallet = await queries.get_tlc_wallet(user_id)
    return wallet.get("tlc_balance", 0.0) if wallet else 0.0

async def redeem_for_tokens(user_id: str, tlc_amount: float, target_agent_id: str) -> dict:
    tokens_to_add = tlc_amount * TLC_TO_TOKEN_RATE
    await deduct_tlc(user_id, tlc_amount)
    await queries.update_agent_token_balance(target_agent_id, tokens_to_add)
    
    await queries.insert_tlc_transaction(
        user_id=user_id,
        type="redeemed_tokens",
        amount=-tlc_amount,
        loan_id=None,
        description=f"Redeemed TLC for {tokens_to_add} tokens on agent {target_agent_id}"
    )
    
    target_agent = await queries.get_agent_by_id(target_agent_id)
    return {
        "tlc_spent": tlc_amount,
        "tokens_received": tokens_to_add,
        "agent_new_balance": target_agent.get("token_balance") if target_agent else 0.0
    }

async def redeem_for_trust(user_id: str, tlc_amount: float, agent_id: str) -> dict:
    trust_boost = (tlc_amount / TLC_TO_TRUST_RATE) * 0.05
    await deduct_tlc(user_id, tlc_amount)
    new_trust = await agent_service.update_trust_score(agent_id, trust_boost)
    
    await queries.insert_tlc_transaction(
        user_id=user_id,
        type="redeemed_trust",
        amount=-tlc_amount,
        loan_id=None,
        description=f"Redeemed TLC for {trust_boost} trust boost on agent {agent_id}"
    )
    
    return {
        "tlc_spent": tlc_amount,
        "trust_boost": trust_boost,
        "agent_new_trust": new_trust
    }
