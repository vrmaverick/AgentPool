# TokenLend — CLAUDE.md

> This file is read by Claude Code at the start of every session.
> Never delete it. Update it as the project evolves.

---

## What This Project Is

**TokenLend** is an AI-native token credit marketplace built on Groq API where:

- Users register their Groq API key (AES-256 encrypted, never returned via API)
- Agents that run out of tokens mid-task automatically borrow from idle users
- Lenders earn **TLC (TokenLend Credits)** — a separate platform currency — NOT tokens directly
- TLC can be redeemed for Groq tokens, used to boost trust score, or Encached (Dummy button)
- Platform earns 0.5% of every loan as TLC (controls supply, earns float)
- A Groq-powered Decision Agent handles matchmaking + risk scoring + City and Timezone (inactive hours midnight)
- All LLM calls route through a proxy that injects the correct real key server-side
- Session continuity is preserved across key switches via the messages[] array

---

## Dual Currency Model — CRITICAL TO UNDERSTAND

There are exactly TWO currencies in this system. Never conflate them.

### Currency 1: Groq Tokens
- Real API compute credits tied to a user's Groq account
- Stored as `token_balance` on the Agent model
- Depleted when the agent makes LLM calls via the proxy
- Replenished when a loan is repaid (borrower returns the principal tokens)
- NOT the yield — principal only comes back as tokens

### Currency 2: TLC (TokenLend Credits)
- Platform-issued dummy currency, stored in `tlc_wallets` table
- Minted ONLY on successful loan repayment
- Amount minted = loan_amount * LENDER_YIELD_PCT (default 5%)
- NEVER minted speculatively — only real completed loans generate TLC
- Platform also mints platform_fee_pct (0.5%) of loan to its own TLC treasury

### The Flow (memorise this)

```
Priya has 900 Groq tokens (idle)
Vedant's agent hits 0 tokens mid-task

Loan created:
  - Priya's token_balance: 900 -> 750  (150 tokens locked for loan)
  - Vedant's token_balance: 0   -> 150 (150 tokens borrowed)
  - Proxy now uses Priya's Groq key for Vedant's calls

Task completes. Repayment:
  - Vedant's token_balance: 150 -> 0   (returns 150 principal)
  - Priya's token_balance:  750 -> 900 (gets 150 principal back)
  - Platform MINTS 7.5 TLC  -> credits Priya's TLC wallet  (5% yield)
  - Platform MINTS 0.75 TLC -> credits platform TLC treasury (0.5% fee)
  - Vedant paid: 150 tokens (his Groq quota cost)
  - Priya earned: 7.5 TLC (redeemable, not tokens directly)

Priya's TLC options:
  - Redeem 100 TLC -> 100 Groq tokens (1:1 rate)
  - Spend 50 TLC  -> +0.05 trust score boost
  - Accumulate    -> future UPI cashout (1000 TLC = ₹1, shown as "coming soon")
```

### Why TLC Not Tokens Directly
1. Prevents infinite token inflation (minting tokens = printing money)
2. TLC is redeemable but controlled — platform governs conversion rate
3. Creates platform stickiness (users have TLC balance, stay in ecosystem)
4. Separation of concerns: compute credits vs reward credits
5. Makes the business model defensible to judges

---

## Directory Structure

```
tokenlend/
├── CLAUDE.md                          <- you are here
├── .env
├── docker-compose.yml
├── README.md
│
├── backend/
│   ├── main.py                        <- FastAPI entry point
│   ├── requirements.txt
│   ├── .env
│   └── app/
│       ├── config.py                  <- env vars, constants, rates
│       ├── db/
│       │   ├── database.py            <- Firebase test and setup, all table creation
│       │   └── queries.py             <- every SQL query as a named async fn
│       ├── models/
│       │   ├── agent.py
│       │   ├── loan.py
│       │   ├── user.py
│       │   ├── proxy_token.py
│       │   └── tlc_wallet.py          <- NEW: TLC wallet + transaction models
│       ├── core/
│       │   ├── vault.py               <- AES-256 encrypt/decrypt/mask Groq keys
│       │   ├── proxy.py               <- HTTP proxy: inject key, track usage
│       │   ├── decision_agent.py      <- Groq-powered loan matchmaking
│       │   └── tlc_engine.py          <- NEW: mint, redeem, transfer TLC
│       ├── services/
│       │   ├── user_service.py        <- register, login, JWT
│       │   ├── agent_service.py       <- register agent, update trust
│       │   ├── loan_service.py        <- loan lifecycle, calls tlc_engine on repay
│       │   └── token_service.py       <- consume tokens, detect exhaustion
│       ├── api/
│       │   ├── users.py
│       │   ├── agents.py
│       │   ├── loans.py
│       │   ├── proxy.py               <- POST /proxy/chat
│       │   ├── wallet.py              <- NEW: GET /wallet, POST /wallet/redeem
│       │   └── demo.py
│       └── middleware/
│           └── auth.py
│
└── frontend/
    └── src/
        └── components/
            ├── wallet/
            │   ├── TLCWalletCard.tsx  <- NEW: TLC balance, earn rate, redeem btn
            │   └── RedeemPanel.tsx    <- NEW: choose redeem option
            ├── dashboard/
            │   ├── StatsBar.tsx       <- add TLC earned stat
            │   └── TxLog.tsx
            ├── agents/
            ├── loans/
            └── proxy/
```

---

## Tech Stack

| Layer      | Choice                            |
|------------|-----------------------------------|
| Backend    | Python 3.11 + FastAPI             |
| Database   | google-cloud-firestore        |
| Encryption | cryptography (Fernet / AES-256)   |
| AI / LLM   | Groq API llama-3.3-70b-versatile  |
| Auth       | JWT via python-jose               |
| Frontend   | React 18 + TypeScript + Vite      |
| State      | Zustand                           |
| Styling    | TailwindCSS                       |

---

## Database Schema — Key Tables

```sql
-- Groq token balances live on agents table
agents (
  id, user_id, name, role,
  encrypted_api_key, api_key_masked,
  token_balance, max_balance,
  trust_score, ...
  location, Time-zone
)

-- TLC is completely separate
tlc_wallets (
  id,
  user_id TEXT UNIQUE,      -- one wallet per user
  tlc_balance REAL,         -- current TLC balance
  total_earned REAL,        -- lifetime earned
  total_redeemed REAL,      -- lifetime redeemed
  updated_at TEXT
)

tlc_transactions (
  id,
  user_id,
  type TEXT,                -- 'earned' | 'redeemed_tokens' | 'redeemed_trust' | 'platform_fee'
  amount REAL,              -- TLC amount
  loan_id TEXT,             -- which loan triggered this (nullable)
  description TEXT,
  created_at TEXT
)

-- Loans track both token flows and TLC to be minted
loans (
  id, lender_agent_id, borrower_agent_id,
  lender_user_id, borrower_user_id,
  amount,                   -- tokens lent
  tlc_yield_amount REAL,    -- TLC to mint on repayment (amount * 0.05)
  platform_tlc_fee REAL,    -- TLC for platform (amount * 0.005)
  status,                   -- 'active' | 'repaid' | 'defaulted'
  start_time, due_time, repaid_at
)
```

---

## Environment Variables

```bash
GROQ_API_KEY=gsk_...
VAULT_SECRET=exactly-32-characters-here!!
JWT_SECRET=your-jwt-secret-here
APP_ENV=development
PROXY_TOKEN_TTL_MINUTES=30
MAX_LOAN_AMOUNT=500
MIN_TRUST_TO_BORROW=0.70
MIN_TRUST_TO_LEND=0.60
PLATFORM_FEE_PCT=0.005       # 0.5% minted to platform treasury
LENDER_YIELD_PCT=0.05        # 5% minted to lender as TLC
TLC_TO_TOKEN_RATE=1.0        # 1 TLC = 1 Groq token on redemption
TLC_TO_TRUST_RATE=50         # 50 TLC = +0.05 trust score
TLC_CASHOUT_RATE=1000        # 1000 TLC = ₹1 (show as "coming soon")
```

---

## TLC Engine Rules

```python
# On successful repayment only — never before
def on_loan_repaid(loan):
    tlc_yield = loan.amount * LENDER_YIELD_PCT       # e.g. 7.5 TLC
    platform_tlc = loan.amount * PLATFORM_FEE_PCT    # e.g. 0.75 TLC

    mint_tlc(user_id=loan.lender_user_id, amount=tlc_yield,
             type='earned', loan_id=loan.id)

    mint_tlc(user_id=PLATFORM_USER_ID, amount=platform_tlc,
             type='platform_fee', loan_id=loan.id)

# Redeem TLC for tokens
def redeem_tlc_for_tokens(user_id, tlc_amount):
    tokens = tlc_amount * TLC_TO_TOKEN_RATE
    deduct_tlc(user_id, tlc_amount)
    # Credit tokens to user's primary agent
    add_tokens(user_id, tokens)

# Redeem TLC for trust score
def redeem_tlc_for_trust(user_id, agent_id, tlc_amount):
    boost = (tlc_amount / TLC_TO_TRUST_RATE) * 0.05
    deduct_tlc(user_id, tlc_amount)
    update_trust_score(agent_id, +boost)
```

---

## API Endpoints

```
POST /user/register
POST /user/login

POST /agent/register        requires JWT
GET  /agents
POST /agent/use_tokens

POST /loan/request          requires JWT — triggers Decision Agent
POST /loan/repay/{id}       requires JWT — triggers TLC minting
GET  /loans

POST /proxy/chat            Auth: Bearer ptk_xxx (NOT a JWT)

GET  /wallet                requires JWT — { tlc_balance, total_earned, history }
POST /wallet/redeem         requires JWT — { type: 'tokens'|'trust', tlc_amount, agent_id? }

POST /demo/seed
POST /demo/run              SSE stream
GET  /demo/state
```

---

## Absolute Rules for Claude Code

1. NEVER return decrypted API keys in any response or log
2. NEVER modify messages[] when proxying
3. NEVER mint TLC before loan is confirmed repaid
4. NEVER deduct tokens before Groq confirms success (check HTTP 200)
5. NEVER allow a user to borrow from their own agents
6. ALWAYS enforce trust score thresholds before loan approval
7. ALWAYS use tlc_engine.py for any TLC operation — never update tlc_balance directly in Firebase outside that module
8. NEVER hardcode VAULT_SECRET, GROQ_API_KEY, JWT_SECRET

---

## Trust Score Rules

| Event                  | Borrower Delta | Lender Delta |
|------------------------|----------------|--------------|
| Repay on time          | +0.02          | +0.005       |
| Late repayment         | -0.05          | 0            |
| Default                | -0.15          | 0            |
| New user baseline      | 0.80           | 0.80         |
| Trust < 0.70           | cannot borrow  |              |
| Trust < 0.60           |                | cannot lend  |

---

## Build Order

```
Phase 1  ->  DB schema + models + vault + TLC wallet tables
Phase 2  ->  User registration + JWT auth
Phase 3  ->  Agent registration with encrypted key storage
Phase 4  ->  Token consumption + exhaustion detection
Phase 5  ->  Loan request + Decision Agent
Phase 6  ->  Proxy endpoint — key injection + usage tracking
Phase 7  ->  Repayment + TLC minting + trust score updates
Phase 8  ->  Wallet API — balance, history, redeem options
Phase 9  ->  Frontend — dashboard + TLC wallet card + redeem panel
Phase 10 ->  Demo scenario + SessionTrace + polish
```