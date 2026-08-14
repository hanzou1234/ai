import uuid
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.contract import Contract, ContractStatus
from app.services.registry import RegistryService

class NegotiationService:
    @staticmethod
    async def propose_contract(db: AsyncSession, buyer_id: str, seller_id: str, task: str, offered_price: float):
        contract_id = str(uuid.uuid4())
        contract = Contract(
            id=contract_id,
            buyer_id=buyer_id,
            seller_id=seller_id,
            task_description=task,
            agreed_price=offered_price,
            status=ContractStatus.NEGOTIATING
        )
        db.add(contract)
        await db.commit()
        await db.refresh(contract)
        return contract

    @staticmethod
    async def accept_proposal(db: AsyncSession, contract_id: str):
        result = await db.execute(select(Contract).where(Contract.id == contract_id))
        contract = result.scalar_one_or_none()
        if contract:
            contract.status = ContractStatus.ESCROWED
            await db.commit()
        return contract
