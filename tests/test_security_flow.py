import base64

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.database import Base
from app.models.agent import Agent
from app.models.contract import ContractStatus
from app.services.negotiation import NegotiationService
from app.services.signatures import canonical_payload


def sign(private_key, action, payload):
    return base64.b64encode(private_key.sign(canonical_payload(action, payload))).decode()


def public_key(private_key):
    return base64.b64encode(private_key.public_key().public_bytes_raw()).decode()


@pytest.mark.asyncio
async def test_high_value_contract_requires_signatures_and_supervisor_approval(tmp_path):
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'security.db'}"
    engine = create_async_engine(database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    buyer_key = Ed25519PrivateKey.generate()
    seller_key = Ed25519PrivateKey.generate()
    buyer_supervisor_key = Ed25519PrivateKey.generate()
    seller_supervisor_key = Ed25519PrivateKey.generate()

    async with session_factory() as session:
        session.add_all([
            Agent(id="buyer", name="Buyer", capabilities={"tags": []}, base_price=10,
                  signing_public_key=public_key(buyer_key), supervisor_public_key=public_key(buyer_supervisor_key)),
            Agent(id="seller", name="Seller", capabilities={"tags": []}, base_price=10,
                  signing_public_key=public_key(seller_key), supervisor_public_key=public_key(seller_supervisor_key)),
        ])
        await session.commit()

        proposal = {"buyer_id": "buyer", "seller_id": "seller", "task": "Research", "offered_price": 25.0}
        contract = await NegotiationService.propose_contract(
            session, **proposal, buyer_signature=sign(buyer_key, "propose_contract", proposal)
        )
        acceptance = {"contract_id": contract.id, "buyer_signature": contract.buyer_signature}
        contract = await NegotiationService.accept_proposal(
            session, contract.id, sign(seller_key, "accept_contract", acceptance)
        )
        assert contract.status == ContractStatus.PENDING_SUPERVISOR

        buyer_approval = {"contract_id": contract.id, "agent_id": "buyer", "decision": "approve"}
        seller_approval = {"contract_id": contract.id, "agent_id": "seller", "decision": "approve"}
        await NegotiationService.approve_by_supervisor(
            session, contract.id, "buyer", sign(buyer_supervisor_key, "supervisor_approval", buyer_approval)
        )
        contract = await NegotiationService.approve_by_supervisor(
            session, contract.id, "seller", sign(seller_supervisor_key, "supervisor_approval", seller_approval)
        )
        assert contract.status == ContractStatus.EXECUTING

        buyer_completion = {"contract_id": contract.id, "agent_id": "buyer", "decision": "complete"}
        seller_completion = {"contract_id": contract.id, "agent_id": "seller", "decision": "complete"}
        await NegotiationService.attest_completion(
            session, contract.id, "buyer", sign(buyer_key, "attest_completion", buyer_completion)
        )
        contract = await NegotiationService.attest_completion(
            session, contract.id, "seller", sign(seller_key, "attest_completion", seller_completion)
        )
        assert contract.status == ContractStatus.COMPLETED

    await engine.dispose()
