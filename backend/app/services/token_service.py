"""
token_service.py — Token consumption and exhaustion detection.

Flow:
  consume_tokens() deducts from token_balance, floors at 0 (never goes negative),
  updates last_active, then returns exhaustion/warning signals.

  should_trigger_loan fires when remaining < 10% of max_balance — gives the
  Decision Agent time to find a lender before the agent fully runs dry.
"""

from fastapi import HTTPException, status

from app.db.queries import (
    get_agent_by_id,
    update_agent_token_balance,
    update_agent_last_active,
)


def _compute_status(remaining: float, max_balance: float) -> str:
    if max_balance <= 0:
        return "exhausted"
    pct = remaining / max_balance
    if remaining == 0:
        return "exhausted"
    if pct < 0.10:
        return "critical"
    if pct <= 0.50:
        return "low"
    return "healthy"


async def consume_tokens(agent_id: str, amount: float) -> dict:
    """
    Deduct `amount` tokens from agent's balance (floors at 0).
    Returns:
      remaining          — balance after deduction
      exhausted          — True when balance hits 0
      should_trigger_loan— True when remaining < 10% of max_balance
      status             — healthy | low | critical | exhausted
    """
    agent = await get_agent_by_id(agent_id)
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found.")

    current: float = float(agent.get("token_balance", 0))
    max_balance: float = float(agent.get("max_balance", 0))

    # Floor deduction at 0 — never drive balance negative
    actual_deduct = min(amount, current)
    remaining = current - actual_deduct  # always >= 0

    # Write the delta (negative) to Firestore via Increment
    if actual_deduct > 0:
        await update_agent_token_balance(agent_id, -actual_deduct)
    else:
        # Still bump last_active even if nothing to deduct
        await update_agent_last_active(agent_id)

    exhausted = remaining == 0
    should_trigger_loan = (max_balance > 0) and (remaining < max_balance * 0.10)
    token_status = _compute_status(remaining, max_balance)

    return {
        "remaining": remaining,
        "exhausted": exhausted,
        "should_trigger_loan": should_trigger_loan,
        "status": token_status,
    }


async def get_token_status(agent_id: str) -> dict:
    """
    Return current balance info without modifying anything.
    """
    agent = await get_agent_by_id(agent_id)
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found.")

    balance: float = float(agent.get("token_balance", 0))
    max_balance: float = float(agent.get("max_balance", 0))
    pct = (balance / max_balance * 100) if max_balance > 0 else 0.0
    token_status = _compute_status(balance, max_balance)

    return {
        "balance": balance,
        "max": max_balance,
        "pct": round(pct, 2),
        "status": token_status,
    }
