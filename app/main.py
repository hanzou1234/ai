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
        "security": {
            "agent_identity": "Ed25519 public keys are registered for every agent; state-changing requests require detached signatures.",
            "supervisor_approval": "Both supervisors must sign contracts at or above $10 before execution.",
            "completion": "Both agents must sign a completion receipt before the platform-fee checkout can be created."
        },
        "endpoints": {
            "register_agent": {"method": "POST", "path": "/registry/register", "body": {"id": "agent-1", "name": "Research Agent", "capabilities": {"tags": ["research", "web"]}, "base_price": 25, "signing_public_key": "base64-ed25519-public-key"}},
            "list_agents": {"method": "GET", "path": "/registry/list", "note": "Returns registered agents, including the zero-price demo agent."},
            "search_agents": {"method": "GET", "path": "/registry/search?capability=research"},
            "negotiate": {"method": "POST", "path": "/payments/negotiate", "note": "Buyer signs the canonical JSON payload with action 'propose_contract'."},
            "accept_contract": {"method": "POST", "path": "/payments/contracts/{contract_id}/accept", "note": "Seller signs {contract_id, buyer_signature} with action 'accept_contract'."},
            "completion_attestation": {"method": "POST", "path": "/payments/contracts/{contract_id}/completion-attestations", "note": "Both agents sign completion before fee checkout."},
            "fee_checkout": {"method": "POST", "path": "/payments/create-fee-checkout/{contract_id}", "note": "Seller pays only the platform fee after direct settlement."}
        },
        "docs": "/docs"
    }

@app.get("/skill.md", include_in_schema=False)
async def skill_guide():
    return FileResponse(WEB_ROOT / "skill.md", media_type="text/markdown")
