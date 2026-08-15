import uuid
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.contract import Contract, ContractStatus
from app.services.registry import RegistryService
from app.services.signatures import verify_signature
from app.config import settings

class NegotiationService:
    @staticmethod
    async def propose_contract(
        db: AsyncSession,
        buyer_id: str,
        seller_id: str,
        task: str,
        offered_price: float,
        buyer_signature: str,
    ):
        buyer = await RegistryService.get_agent(db, buyer_id)
        seller = await RegistryService.get_agent(db, seller_id)
        if not buyer or not seller:
            raise ValueError("Both agents must be registered")
        payload = {
            "buyer_id": buyer_id,
            "seller_id": seller_id,
            "task": task,
            "offered_price": offered_price,
        }
        if not verify_signature(buyer.signing_public_key, "propose_contract", payload, buyer_signature):
            raise ValueError("Invalid buyer signature")
        contract_id = str(uuid.uuid4())
        contract = Contract(
            id=contract_id,
            buyer_id=buyer_id,
            seller_id=seller_id,
            task_description=task,
            agreed_price=offered_price,
            status=ContractStatus.NEGOTIATING,
            buyer_signature=buyer_signature,
        )
        db.add(contract)
        await db.commit()
        await db.refresh(contract)
        return contract

    @staticmethod
    async def accept_proposal(db: AsyncSession, contract_id: str, seller_signature: str):
        result = await db.execute(select(Contract).where(Contract.id == contract_id))
        contract = result.scalar_one_or_none()
        if not contract:
            raise ValueError("Contract not found")
        if contract.status != ContractStatus.NEGOTIATING:
            raise ValueError("Contract is not awaiting seller acceptance")
        seller = await RegistryService.get_agent(db, contract.seller_id)
        payload = {"contract_id": contract.id, "buyer_signature": contract.buyer_signature}
        if not seller or not verify_signature(seller.signing_public_key, "accept_contract", payload, seller_signature):
            raise ValueError("Invalid seller signature")
        contract.seller_signature = seller_signature
        contract.status = (
            ContractStatus.PENDING_SUPERVISOR
            if contract.agreed_price >= settings.SUPERVISOR_APPROVAL_THRESHOLD_USD
            else ContractStatus.EXECUTING
        )
        await db.commit()
        return contract

    @staticmethod
    async def approve_by_supervisor(db: AsyncSession, contract_id: str, agent_id: str, signature: str):
        result = await db.execute(select(Contract).where(Contract.id == contract_id))
        contract = result.scalar_one_or_none()
        if not contract or contract.status != ContractStatus.PENDING_SUPERVISOR:
            raise ValueError("Contract is not awaiting supervisor approval")
        if agent_id not in (contract.buyer_id, contract.seller_id):
            raise ValueError("Agent is not a party to this contract")
        agent = await RegistryService.get_agent(db, agent_id)
        if not agent or not agent.supervisor_public_key:
            raise ValueError("Agent has no registered supervisor key")
        payload = {"contract_id": contract.id, "agent_id": agent_id, "decision": "approve"}
        if not verify_signature(agent.supervisor_public_key, "supervisor_approval", payload, signature):
            raise ValueError("Invalid supervisor signature")
        if agent_id == contract.buyer_id:
            contract.buyer_supervisor_signature = signature
        else:
            contract.seller_supervisor_signature = signature
        if contract.buyer_supervisor_signature and contract.seller_supervisor_signature:
            contract.status = ContractStatus.EXECUTING
        await db.commit()
        return contract

    @staticmethod
    async def attest_completion(db: AsyncSession, contract_id: str, agent_id: str, signature: str):
        result = await db.execute(select(Contract).where(Contract.id == contract_id))
        contract = result.scalar_one_or_none()
        if not contract or contract.status != ContractStatus.EXECUTING:
            raise ValueError("Contract is not executing")
        if agent_id not in (contract.buyer_id, contract.seller_id):
            raise ValueError("Agent is not a party to this contract")
        agent = await RegistryService.get_agent(db, agent_id)
        payload = {"contract_id": contract.id, "agent_id": agent_id, "decision": "complete"}
        if not agent or not verify_signature(agent.signing_public_key, "attest_completion", payload, signature):
            raise ValueError("Invalid completion signature")
        if agent_id == contract.buyer_id:
            contract.buyer_completion_signature = signature
        else:
            contract.seller_completion_signature = signature
        if contract.buyer_completion_signature and contract.seller_completion_signature:
            contract.status = ContractStatus.COMPLETED
        await db.commit()
        return contract
