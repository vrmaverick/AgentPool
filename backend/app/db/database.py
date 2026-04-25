"""
database.py — Firestore async client + collection name constants.

Collection layout (schema-less; fields shown as reference):

  USERS            {id, name, email, hashed_password, created_at}
  AGENTS           {id, user_id, name, role,
                    encrypted_api_key, api_key_masked,
                    token_balance, max_balance,
                    trust_score, loans_taken, loans_given, repayments_ok,
                    usage_rate, last_active, created_at,
                    location, timezone, preferred_start_hour, preferred_end_hour}
  LOANS            {id, lender_agent_id, borrower_agent_id,
                    lender_user_id, borrower_user_id,
                    amount, tlc_yield_amount, platform_tlc_fee,
                    status, start_time, due_time, repaid_at}
  PROXY_TOKENS     {id, agent_id, user_id, credits_remaining,
                    created_at, expires_at}
  TLC_WALLETS      {id, user_id, tlc_balance, total_earned,
                    total_redeemed, updated_at}
  TLC_TRANSACTIONS {id, user_id, type, amount, loan_id,
                    description, created_at}
  TX_LOG           {id, event_type, actor_user_id, related_id,
                    description, created_at}
"""

from google.cloud import firestore
from app.config import GCP_PROJECT_ID

# Async Firestore client — shared singleton
db: firestore.AsyncClient = firestore.AsyncClient(project=GCP_PROJECT_ID)

# ── Collection name constants ─────────────────────────────────────────────────
USERS = "users"
AGENTS = "agents"
LOANS = "loans"
PROXY_TOKENS = "proxy_tokens"
TLC_WALLETS = "tlc_wallets"
TLC_TRANSACTIONS = "tlc_transactions"
TX_LOG = "tx_log"
