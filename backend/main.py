"""
main.py — TokenLend FastAPI entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.users import router as users_router
from app.api.agents import router as agents_router

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
