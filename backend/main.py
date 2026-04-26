"""
main.py — TokenLend FastAPI entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.users import router as users_router
from app.api.agents import router as agents_router
from app.api.loans import router as loans_router
from app.api.proxy import router as proxy_router
from app.api.wallet import router as wallet_router
from app.api.demo import router as demo_router

app = FastAPI(title="TokenLend", version="2.0")

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(users_router, prefix="/user", tags=["users"])
app.include_router(agents_router, prefix="/agent", tags=["agents"])
app.include_router(loans_router, prefix="/loan", tags=["loans"])
app.include_router(proxy_router, prefix="/proxy", tags=["proxy"])
app.include_router(wallet_router, prefix="/wallet", tags=["wallet"])
app.include_router(demo_router, prefix="/demo", tags=["demo"])


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.0", "currencies": ["tokens", "TLC"]}


# ── Startup ───────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    from app.db.database import db
    try:
        # Lightweight ping: list up to 1 doc from any collection
        async for _ in db.collection("users").limit(1).stream():
            break
        print("[TokenLend] Firestore connection OK")
    except Exception as e:
        print(f"[TokenLend] WARNING: Firestore ping failed — {e}")
