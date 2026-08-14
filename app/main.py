from fastapi import FastAPI
from app.database import init_db
from app.routers import registry, escrow, legal, stripe, kyc # 新しく追加
from app.config import settings
import logging

logging.basicConfig(level=settings.LOG_LEVEL)

app = FastAPI(title="Agent Economy Engine - P2P Platform")

@app.on_event("startup")
async def on_startup():
    await init_db()

app.include_router(registry.router)
app.include_router(escrow.router)
app.include_router(legal.router)
app.include_router(stripe.router, prefix="/stripe", tags=["Stripe Webhook"]) # 新しく追加
app.include_router(kyc.router, prefix="/kyc", tags=["KYC & Onboarding"]) # 新しく追加

@app.get("/")
async def root():
    return {
        "message": "Agent Economy Engine PoC is running",
        "model": "P2P Decentralized Payment Model",
        "legal_docs": "/legal/terms, /legal/privacy, /legal/aml-policy, /legal/disclaimer",
        "docs": "/docs"
    }
