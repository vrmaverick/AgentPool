"""
queries.py — Every Firestore operation as a named async function.

Rules:
  - Use firestore.Increment(delta) for all numeric balance changes.
  - Use db.batch() for multi-document atomic operations.
  - Auto-IDs: db.collection(X).document() — id is stored inside the doc too.
  - Timestamps: ISO 8601 strings (datetime.utcnow().isoformat() + "Z").
  - Queries: .where("field", "==", val).stream() — no raw SQL.
"""

from datetime import datetime
from typing import Optional, AsyncIterator
from google.cloud import firestore

from app.db.database import (
    db,
    USERS, AGENTS, LOANS, PROXY_TOKENS,
    TLC_WALLETS, TLC_TRANSACTIONS, TX_LOG,
)


def _now() -> str:
    return datetime.utcnow().isoformat() + "Z"


# ── helpers ───────────────────────────────────────────────────────────────────

async def _doc_to_dict(ref) -> Optional[dict]:
    snap = await ref.get()
    if snap.exists:
        return snap.to_dict()
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# USERS
# ═══════════════════════════════════════════════════════════════════════════════

async def create_user(
    name: str,
    email: str,
    hashed_password: str,
    city: str | None = None,
    timezone: str | None = None,
) -> dict:
    ref = db.collection(USERS).document()
    doc = {
        "id": ref.id,
        "name": name,
        "email": email,
        "hashed_password": hashed_password,
        "city": city,
        "timezone": timezone,
        "created_at": _now(),
    }
    await ref.set(doc)
    return doc

async def get_user_by_email(email: str) -> Optional[dict]:
    docs = db.collection(USERS).where("email", "==", email).limit(1).stream()
    async for snap in docs:
        return snap.to_dict()
    return None


async def get_user_by_id(user_id: str) -> Optional[dict]:
    return await _doc_to_dict(db.collection(USERS).document(user_id))


# ═══════════════════════════════════════════════════════════════════════════════
# AGENTS
# ═══════════════════════════════════════════════════════════════════════════════

async def create_agent(
    user_id: str,
    name: str,
    role: str,
    encrypted_api_key: str,
    api_key_masked: str,
    max_balance: float,
    location: Optional[str] = None,
    timezone: Optional[str] = None,
    preferred_start_hour: Optional[int] = None,
    preferred_end_hour: Optional[int] = None,
) -> dict:
    ref = db.collection(AGENTS).document()
    doc = {
        "id": ref.id,
        "user_id": user_id,
        "name": name,
        "role": role,
        "encrypted_api_key": encrypted_api_key,
        "api_key_masked": api_key_masked,
        "token_balance": max_balance,
        "max_balance": max_balance,
        "trust_score": 0.80,
        "loans_taken": 0,
        "loans_given": 0,
        "repayments_ok": 0,
        "usage_rate": 0.0,
        "last_active": None,
        "created_at": _now(),
    }
    await ref.set(doc)
    return doc


async def get_agent_by_id(agent_id: str) -> Optional[dict]:
    return await _doc_to_dict(db.collection(AGENTS).document(agent_id))


async def get_agents_by_user(user_id: str) -> list[dict]:
    result = []
    async for snap in db.collection(AGENTS).where("user_id", "==", user_id).stream():
        result.append(snap.to_dict())
    return result


async def get_all_agents() -> list[dict]:
    result = []
    async for snap in db.collection(AGENTS).stream():
        result.append(snap.to_dict())
    return result


async def update_agent_token_balance(agent_id: str, delta: float) -> None:
    """Use Increment — never overwrite the whole field."""
    await db.collection(AGENTS).document(agent_id).update({
        "token_balance": firestore.Increment(delta),
        "last_active": _now(),
    })


async def update_agent_trust_score(agent_id: str, delta: float) -> None:
    """Increment trust score by delta (no clamping — use set_agent_trust_score for clamped writes)."""
    await db.collection(AGENTS).document(agent_id).update({
        "trust_score": firestore.Increment(delta),
    })


async def set_agent_trust_score(agent_id: str, value: float) -> None:
    """Write an absolute trust score value. Use this when clamping is required."""
    await db.collection(AGENTS).document(agent_id).update({
        "trust_score": value,
    })


async def update_agent_last_active(agent_id: str) -> None:
    await db.collection(AGENTS).document(agent_id).update({
        "last_active": _now(),
    })


# ═══════════════════════════════════════════════════════════════════════════════
# LOANS
# ═══════════════════════════════════════════════════════════════════════════════

async def create_loan(
    lender_agent_id: str,
    borrower_agent_id: str,
    lender_user_id: str,
    borrower_user_id: str,
    amount: float,
    tlc_yield_amount: float,
    platform_tlc_fee: float,
    due_time: str,
) -> dict:
    ref = db.collection(LOANS).document()
    doc = {
        "id": ref.id,
        "lender_agent_id": lender_agent_id,
        "borrower_agent_id": borrower_agent_id,
        "lender_user_id": lender_user_id,
        "borrower_user_id": borrower_user_id,
        "amount": amount,
        "tlc_yield_amount": tlc_yield_amount,
        "platform_tlc_fee": platform_tlc_fee,
        "status": "active",
        "start_time": _now(),
        "due_time": due_time,
        "repaid_at": None,
    }
    await ref.set(doc)
    return doc


async def get_loan_by_id(loan_id: str) -> Optional[dict]:
    return await _doc_to_dict(db.collection(LOANS).document(loan_id))


async def get_loans_by_user(user_id: str) -> list[dict]:
    result = []
    async for snap in db.collection(LOANS).where("lender_user_id", "==", user_id).stream():
        result.append(snap.to_dict())
    async for snap in db.collection(LOANS).where("borrower_user_id", "==", user_id).stream():
        d = snap.to_dict()
        if not any(r["id"] == d["id"] for r in result):
            result.append(d)
    return result


async def get_all_loans() -> list[dict]:
    result = []
    async for snap in db.collection(LOANS).stream():
        result.append(snap.to_dict())
    return result


async def update_loan_status(loan_id: str, status: str, repaid_at: Optional[str] = None) -> None:
    update = {"status": status}
    if repaid_at:
        update["repaid_at"] = repaid_at
    await db.collection(LOANS).document(loan_id).update(update)


async def get_active_loans() -> list[dict]:
    result = []
    async for snap in db.collection(LOANS).where("status", "==", "active").stream():
        result.append(snap.to_dict())
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# PROXY TOKENS
# ═══════════════════════════════════════════════════════════════════════════════

async def create_proxy_token(
    token_id: str,
    agent_id: str,
    user_id: str,
    credits_remaining: float,
    expires_at: str,
    key_source: str = "self",
    loan_id: Optional[str] = None,
    lender_user_id: Optional[str] = None,
) -> dict:
    ref = db.collection(PROXY_TOKENS).document(token_id)
    doc = {
        "id": token_id,
        "agent_id": agent_id,
        "user_id": user_id,
        "credits_remaining": credits_remaining,
        "created_at": _now(),
        "expires_at": expires_at,
        "key_source": key_source,
        "loan_id": loan_id,
        "lender_user_id": lender_user_id,
    }
    await ref.set(doc)
    return doc


async def get_proxy_token(token_id: str) -> Optional[dict]:
    return await _doc_to_dict(db.collection(PROXY_TOKENS).document(token_id))


async def update_proxy_token_credits(token_id: str, delta: float) -> None:
    await db.collection(PROXY_TOKENS).document(token_id).update({
        "credits_remaining": firestore.Increment(delta),
    })


async def delete_proxy_token(token_id: str) -> None:
    await db.collection(PROXY_TOKENS).document(token_id).delete()

async def expire_proxy_tokens_by_loan_id(loan_id: str) -> None:
    docs = db.collection(PROXY_TOKENS).where("loan_id", "==", loan_id).stream()
    async for snap in docs:
        await snap.reference.update({"credits_remaining": 0, "expires_at": _now()})


# ═══════════════════════════════════════════════════════════════════════════════
# TLC WALLETS & TRANSACTIONS
# ═══════════════════════════════════════════════════════════════════════════════

async def get_tlc_wallet(user_id: str) -> Optional[dict]:
    """Return the TLC wallet doc for a user, or None if it doesn't exist yet."""
    docs = db.collection(TLC_WALLETS).where("user_id", "==", user_id).limit(1).stream()
    async for snap in docs:
        return snap.to_dict()
    return None


async def upsert_tlc_wallet(
    user_id: str,
    tlc_delta: float,
    earned_delta: float = 0.0,
    redeemed_delta: float = 0.0,
) -> None:
    """
    Atomically increment TLC wallet fields.
    Creates the wallet document if it does not yet exist (merge=True sets
    Increment fields on a missing doc to their delta value).
    """
    # Find existing doc by user_id, or create a new one
    query = db.collection(TLC_WALLETS).where("user_id", "==", user_id).limit(1)
    snap_list = []
    async for snap in query.stream():
        snap_list.append(snap)

    if snap_list:
        ref = snap_list[0].reference
    else:
        ref = db.collection(TLC_WALLETS).document()
        # Initialise so that Increment works on the first call
        await ref.set({
            "id": ref.id,
            "user_id": user_id,
            "tlc_balance": 0.0,
            "total_earned": 0.0,
            "total_redeemed": 0.0,
            "updated_at": _now(),
        })

    await ref.update({
        "tlc_balance": firestore.Increment(tlc_delta),
        "total_earned": firestore.Increment(earned_delta),
        "total_redeemed": firestore.Increment(redeemed_delta),
        "updated_at": _now(),
    })


async def insert_tlc_transaction(
    user_id: str,
    type: str,
    amount: float,
    loan_id: Optional[str],
    description: str,
) -> dict:
    ref = db.collection(TLC_TRANSACTIONS).document()
    doc = {
        "id": ref.id,
        "user_id": user_id,
        "type": type,
        "amount": amount,
        "loan_id": loan_id,
        "description": description,
        "created_at": _now(),
    }
    await ref.set(doc)
    return doc


async def get_tlc_history(user_id: str, limit: int = 50) -> list[dict]:
    result = []
    query = (
        db.collection(TLC_TRANSACTIONS)
        .where("user_id", "==", user_id)
        .order_by("created_at", direction=firestore.Query.DESCENDING)
        .limit(limit)
    )
    async for snap in query.stream():
        result.append(snap.to_dict())
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# TX LOG  (general audit trail)
# ═══════════════════════════════════════════════════════════════════════════════

async def insert_tx_log(
    event_type: str,
    actor_user_id: str,
    related_id: Optional[str],
    description: str,
) -> dict:
    ref = db.collection(TX_LOG).document()
    doc = {
        "id": ref.id,
        "event_type": event_type,
        "actor_user_id": actor_user_id,
        "related_id": related_id,
        "description": description,
        "created_at": _now(),
    }
    await ref.set(doc)
    return doc


async def get_tx_log(limit: int = 100) -> list[dict]:
    result = []
    query = (
        db.collection(TX_LOG)
        .order_by("created_at", direction=firestore.Query.DESCENDING)
        .limit(limit)
    )
    async for snap in query.stream():
        result.append(snap.to_dict())
    return result
