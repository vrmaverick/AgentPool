"""
agents.py — /agent/register, /agents, /agent/use_tokens endpoints.

RULE: encrypted_api_key and groq_api_key are NEVER returned in any response.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.middleware.auth import get_current_user
from app.services.agent_service import register_agent, list_agents
from app.services.token_service import consume_tokens, get_token_status

router = APIRouter()


class AgentRegisterBody(BaseModel):
    name: str
    role: str
    groq_api_key: str
    token_balance: float


class UseTokensBody(BaseModel):
    agent_id: str
    amount: float


@router.post("/register")
async def register(
    body: AgentRegisterBody,
    user_id: str = Depends(get_current_user),
):
    agent = await register_agent(
        user_id=user_id,
        name=body.name,
        role=body.role,
        groq_api_key=body.groq_api_key,
        token_balance=body.token_balance,
    )
    return {
        "agent_id": agent["id"],
        "name": agent["name"],
        "api_key_masked": agent["api_key_masked"],
        "trust_score": agent["trust_score"],
        "token_balance": agent["token_balance"],
    }


@router.get("")
async def get_agents():
    """Public — no auth required. Masked keys only."""
    return await list_agents()


@router.get("/{agent_id}/status")
async def agent_status(agent_id: str):
    """Check current token balance and status for a single agent."""
    return await get_token_status(agent_id)


@router.post("/use_tokens")
async def use_tokens(body: UseTokensBody):
    """
    Deduct tokens from an agent. Public endpoint (called by agent runtime).
    Returns exhaustion signals so the caller can decide to request a loan.
    """
    result = await consume_tokens(agent_id=body.agent_id, amount=body.amount)
    return {
        "agent_id": body.agent_id,
        "remaining": result["remaining"],
        "exhausted": result["exhausted"],
        "should_trigger_loan": result["should_trigger_loan"],
        "status": result["status"],
    }
