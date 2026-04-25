"""
agent_service.py — Agent registration, retrieval, trust score management.

SECURITY RULES:
  - encrypted_api_key is NEVER returned to any caller.
  - get_decrypted_key() is INTERNAL ONLY — never call from API layer.
"""

from fastapi import HTTPException, status

from app.core.vault import encrypt_key, decrypt_key, mask_key
from app.db.queries import (
    create_agent,
    get_agent_by_id,
    get_all_agents,
    set_agent_trust_score,
)

_VALID_ROLES = {"pipeline", "lender"}


def _safe_agent(doc: dict) -> dict:
    """Return agent dict with encrypted_api_key stripped. Safe to return from API."""
    d = dict(doc)
    d.pop("encrypted_api_key", None)
    return d


async def register_agent(
    user_id: str,
    name: str,
    role: str,
    groq_api_key: str,
    token_balance: float,
) -> dict:
    """
    Encrypt key, create agent doc, return safe (masked) agent dict.
    Raises 400 on invalid role.
    """
    if role not in _VALID_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role '{role}'. Must be one of: {sorted(_VALID_ROLES)}.",
        )

    encrypted = encrypt_key(groq_api_key)
    masked = mask_key(groq_api_key)

    doc = await create_agent(
        user_id=user_id,
        name=name,
        role=role,
        encrypted_api_key=encrypted,
        api_key_masked=masked,
        max_balance=token_balance,
    )
    return _safe_agent(doc)


async def get_agent(agent_id: str) -> dict:
    """Return agent by ID. Raises 404 if not found. Masked key only."""
    doc = await get_agent_by_id(agent_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found.")
    return _safe_agent(doc)


async def list_agents() -> list[dict]:
    """Return all agents. Masked keys only — never encrypted_api_key."""
    docs = await get_all_agents()
    return [_safe_agent(d) for d in docs]


async def update_trust_score(agent_id: str, delta: float) -> float:
    """
    Apply delta to agent's trust_score, clamped to [0.0, 1.0].
    Returns the new clamped value.
    Raises 404 if agent not found.
    """
    doc = await get_agent_by_id(agent_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found.")

    current = float(doc.get("trust_score", 0.80))
    new_score = max(0.0, min(1.0, current + delta))
    await set_agent_trust_score(agent_id, new_score)
    return new_score


async def get_decrypted_key(agent_id: str) -> str:
    """
    INTERNAL ONLY — decrypt and return the plaintext Groq API key.
    NEVER call this from any API route handler.
    Only call from: proxy.py, decision_agent.py (server-side key injection).
    """
    doc = await get_agent_by_id(agent_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found.")
    encrypted = doc.get("encrypted_api_key")
    if not encrypted:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Agent has no stored API key.",
        )
    return decrypt_key(encrypted)
