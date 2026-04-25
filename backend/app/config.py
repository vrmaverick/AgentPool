import os
import hashlib
import base64
from dotenv import load_dotenv

load_dotenv()

# ── Raw secrets ──────────────────────────────────────────────────────────────
GROQ_API_KEY: str = os.environ["GROQ_API_KEY"]
VAULT_SECRET: str = os.environ["VAULT_SECRET"]
JWT_SECRET: str = os.environ["JWT_SECRET"]
GCP_PROJECT_ID: str = os.environ["GCP_PROJECT_ID"]

# ── Derive Fernet key from VAULT_SECRET (SHA-256 → urlsafe-b64, 32 bytes) ───
_vault_bytes = VAULT_SECRET.encode()
_digest = hashlib.sha256(_vault_bytes).digest()       # 32 raw bytes
FERNET_KEY: bytes = base64.urlsafe_b64encode(_digest) # 44-char b64 Fernet key

# ── App settings ─────────────────────────────────────────────────────────────
APP_ENV: str = os.getenv("APP_ENV", "development")
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

# ── Proxy / loan limits ───────────────────────────────────────────────────────
PROXY_TOKEN_TTL_MINUTES: int = int(os.getenv("PROXY_TOKEN_TTL_MINUTES", "30"))
MAX_LOAN_AMOUNT: float = float(os.getenv("MAX_LOAN_AMOUNT", "500"))
MIN_TRUST_TO_BORROW: float = float(os.getenv("MIN_TRUST_TO_BORROW", "0.70"))
MIN_TRUST_TO_LEND: float = float(os.getenv("MIN_TRUST_TO_LEND", "0.60"))

# ── TLC rates ─────────────────────────────────────────────────────────────────
LENDER_YIELD_PCT: float = float(os.getenv("LENDER_YIELD_PCT", "0.05"))
PLATFORM_FEE_PCT: float = float(os.getenv("PLATFORM_FEE_PCT", "0.005"))
TLC_TO_TOKEN_RATE: float = float(os.getenv("TLC_TO_TOKEN_RATE", "1.0"))
TLC_TO_TRUST_RATE: float = float(os.getenv("TLC_TO_TRUST_RATE", "50"))
TLC_CASHOUT_RATE: float = float(os.getenv("TLC_CASHOUT_RATE", "1000"))

# ── Platform treasury user ID ─────────────────────────────────────────────────
PLATFORM_USER_ID: str = os.getenv("PLATFORM_USER_ID", "platform-treasury")

# ── Service URLs ──────────────────────────────────────────────────────────────
BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8000")
FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
