import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.agent import Agent
from app.models.contract import Contract, ContractStatus
from app.models.transaction import Transaction
from app.config import settings

class EscrowService:
    @staticmethod
    async def deposit_escrow(db: AsyncSession, contract_id: str):
        result = await db.execute(select(Contract).where(Contract.id == contract_id))
        contract = result.scalar_one_or_none()
        if not contract:
            raise ValueError("Contract not found")

        # In a real app, we'd check buyer's balance here
        tx = Transaction(
            id=str(uuid.uuid4()),
            contract_id=contract_id,
            gross_amount=contract.agreed_price,
            platform_fee=0.0,
            seller_net_payout=0.0,
            type="ESCROW_DEPOSIT"
        )
        db.add(tx)
        contract.status = ContractStatus.EXECUTING
        await db.commit()
        return tx

    @staticmethod
    async def settle_payment(db: AsyncSession, contract_id: str):
        result = await db.execute(select(Contract).where(Contract.id == contract_id))
        contract = result.scalar_one_or_none()
        if not contract or contract.status != ContractStatus.EXECUTING:
            raise ValueError("Invalid contract state for settlement")

        gross_amount = contract.agreed_price
        fee_rate = settings.PLATFORM_FEE_RATE
        min_fee = settings.MINIMUM_PLATFORM_FEE
        
        # 手数料計算：最小手数料を適用
        calculated_fee = round(gross_amount * fee_rate, 2)
        platform_fee = max(calculated_fee, min_fee)
        seller_net_payout = gross_amount - platform_fee

        # Update seller balance
        seller_result = await db.execute(select(Agent).where(Agent.id == contract.seller_id))
        seller = seller_result.scalar_one()
        seller.wallet_balance += seller_net_payout

        tx = Transaction(
            id=str(uuid.uuid4()),
            contract_id=contract_id,
            gross_amount=gross_amount,
            platform_fee=platform_fee,
            seller_net_payout=seller_net_payout,
            type="PAYOUT"
        )
        db.add(tx)
        contract.status = ContractStatus.COMPLETED
        await db.commit()
        return tx
