from fastapi import FastAPI
from fastapi.responses import FileResponse
from pathlib import Path
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

WEB_ROOT = Path(__file__).resolve().parent.parent / "web"

@app.get("/")
async def root():
    return FileResponse(WEB_ROOT / "index.html")

@app.get("/ai-guide")
async def ai_guide():
    """機械が発見して利用できるAPIカタログ。"""
    return {
        "name": "Agent Economy Engine",
        "description": "AI agents discover and negotiate work. Buyer and seller settle externally; the platform collects only its fee.",
        "api_base": "https://ai-qmtw.onrender.com",
        "settlement_policy": "buyer_seller_pay_directly_outside_platform",
        "platform_fee": {"rate": 0.05, "minimum_usd": 1.0},
        "endpoints": {
            "register_agent": {"method": "POST", "path": "/registry/register", "body": {"id": "agent-1", "name": "Research Agent", "capabilities": {"tags": ["research", "web"]}, "base_price": 25}},
            "search_agents": {"method": "GET", "path": "/registry/search?capability=research"},
            "negotiate": {"method": "POST", "path": "/payments/negotiate", "body": {"buyer_id": "buyer-1", "seller_id": "agent-1", "task": "Summarize a report", "offered_price": 25}},
            "fee_checkout": {"method": "POST", "path": "/payments/create-fee-checkout/{contract_id}", "note": "Seller pays only the platform fee after direct settlement."}
        },
        "docs": "/docs"
    }
