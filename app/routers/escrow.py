from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.escrow import EscrowService
from app.services.negotiation import NegotiationService
from pydantic import BaseModel

router = APIRouter(prefix="/escrow", tags=["Escrow & Settlement"])

class NegotiationRequest(BaseModel):
    buyer_id: str
    seller_id: str
    task: str
    offered_price: float

@router.post("/negotiate")
async def negotiate(req: NegotiationRequest, db: AsyncSession = Depends(get_db)):
    # Simple auto-accept for PoC
    contract = await NegotiationService.propose_contract(db, req.buyer_id, req.seller_id, req.task, req.offered_price)
    await NegotiationService.accept_proposal(db, contract.id)
    return contract

@router.post("/deposit/{contract_id}")
async def deposit(contract_id: str, db: AsyncSession = Depends(get_db)):
    return await EscrowService.deposit_escrow(db, contract_id)

@router.post("/settle/{contract_id}")
async def settle(contract_id: str, db: AsyncSession = Depends(get_db)):
    return await EscrowService.settle_payment(db, contract_id)
