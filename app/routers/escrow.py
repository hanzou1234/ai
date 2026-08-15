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
    buyer_signature: str

class ContractAcceptanceRequest(BaseModel):
    seller_signature: str

class SupervisorApprovalRequest(BaseModel):
    agent_id: str
    signature: str

class CompletionAttestationRequest(BaseModel):
    agent_id: str
    signature: str

class PaymentCompletionRequest(BaseModel):
    contract_id: str

class DisputeRequest(BaseModel):
    contract_id: str
    reason: str

@router.post("/negotiate")
async def negotiate(req: NegotiationRequest, db: AsyncSession = Depends(get_db)):
    """ネゴシエーション・契約作成"""
    try:
        contract = await NegotiationService.propose_contract(
            db, req.buyer_id, req.seller_id, req.task, req.offered_price, req.buyer_signature
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return contract

@router.post("/contracts/{contract_id}/accept")
async def accept_contract(contract_id: str, req: ContractAcceptanceRequest, db: AsyncSession = Depends(get_db)):
    try:
        return await NegotiationService.accept_proposal(db, contract_id, req.seller_signature)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

@router.post("/contracts/{contract_id}/supervisor-approvals")
async def approve_contract(contract_id: str, req: SupervisorApprovalRequest, db: AsyncSession = Depends(get_db)):
    try:
        return await NegotiationService.approve_by_supervisor(db, contract_id, req.agent_id, req.signature)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

@router.post("/contracts/{contract_id}/completion-attestations")
async def attest_completion(contract_id: str, req: CompletionAttestationRequest, db: AsyncSession = Depends(get_db)):
    try:
        return await NegotiationService.attest_completion(db, contract_id, req.agent_id, req.signature)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

@router.post("/create-fee-checkout/{contract_id}")
@router.post("/create-payment-link/{contract_id}", include_in_schema=False)
async def create_payment_link(contract_id: str, db: AsyncSession = Depends(get_db)):
    """売買代金ではなく、セラーが支払うプラットフォーム手数料のCheckoutを生成する。"""
    try:
        payment_data = await P2PPaymentService.create_platform_fee_checkout(db, contract_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return {
        "payment_link": payment_data,
        "message": "買い手と売り手の決済は当事者間で行い、売り手は表示された5%のプラットフォーム手数料だけを支払ってください。"
    }

@router.get("/fee-success")
async def fee_success():
    return {"message": "Platform fee payment received."}

@router.get("/fee-cancelled")
async def fee_cancelled():
    return {"message": "Platform fee payment was cancelled."}

@router.post("/complete-payment")
async def complete_payment(req: PaymentCompletionRequest, db: AsyncSession = Depends(get_db)):
    """旧互換エンドポイント。Stripe Checkout完了はWebhookで記録する。"""
    raise HTTPException(status_code=410, detail="Use /payments/create-payment-link/{contract_id}; buyer-seller payment is outside this platform.")

@router.post("/report-dispute")
async def report_dispute(req: DisputeRequest, db: AsyncSession = Depends(get_db)):
    """紛争報告：Stripe/PayPalの紛争解決機能を使用"""
    result = await P2PPaymentService.refund_if_dispute(db, req.contract_id, req.reason)
    return result

