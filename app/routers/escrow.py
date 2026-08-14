from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.escrow import P2PPaymentService
from app.services.negotiation import NegotiationService
from pydantic import BaseModel

router = APIRouter(prefix="/payments", tags=["P2P Payments"])

class NegotiationRequest(BaseModel):
    buyer_id: str
    seller_id: str
    task: str
    offered_price: float

class PaymentCompletionRequest(BaseModel):
    contract_id: str

class DisputeRequest(BaseModel):
    contract_id: str
    reason: str

@router.post("/negotiate")
async def negotiate(req: NegotiationRequest, db: AsyncSession = Depends(get_db)):
    """ネゴシエーション・契約作成"""
    contract = await NegotiationService.propose_contract(db, req.buyer_id, req.seller_id, req.task, req.offered_price)
    await NegotiationService.accept_proposal(db, contract.id)
    return contract

@router.post("/create-payment-link/{contract_id}")
async def create_payment_link(contract_id: str, db: AsyncSession = Depends(get_db)):
    """バイヤー向け支払いリンク生成（P2P直接決済）"""
    payment_data = await P2PPaymentService.create_payment_link(db, contract_id)
    return {
        "payment_link": payment_data,
        "message": "バイヤーはセラーに直接支払ってください。決済完了後に /complete-payment を呼び出してください。"
    }

@router.post("/complete-payment")
async def complete_payment(req: PaymentCompletionRequest, db: AsyncSession = Depends(get_db)):
    """支払い完了：プラットフォーム手数料を自動徴収"""
    tx = await P2PPaymentService.record_payment_completion(db, req.contract_id)
    return {
        "message": "Payment completed and platform fee collected",
        "transaction": tx
    }

@router.post("/report-dispute")
async def report_dispute(req: DisputeRequest, db: AsyncSession = Depends(get_db)):
    """紛争報告：Stripe/PayPalの紛争解決機能を使用"""
    result = await P2PPaymentService.refund_if_dispute(db, req.contract_id, req.reason)
    return result

