from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.agent import Agent
from typing import List, Optional

class RegistryService:
    @staticmethod
    async def register_agent(
        db: AsyncSession,
        agent_id: str,
        name: str,
        capabilities: dict,
        base_price: float,
        signing_public_key: str | None = None,
        supervisor_public_key: str | None = None,
    ):
        agent = Agent(
            id=agent_id,
            name=name,
            capabilities=capabilities,
            base_price=base_price,
            signing_public_key=signing_public_key,
            supervisor_public_key=supervisor_public_key,
        )
        db.add(agent)
        await db.commit()
        await db.refresh(agent)
        return agent

    @staticmethod
    async def find_agents(db: AsyncSession, capability: str) -> List[Agent]:
        # Simple implementation: check if capability string is in the capabilities dict
        result = await db.execute(select(Agent))
        agents = result.scalars().all()
        return [a for a in agents if capability in a.capabilities.get("tags", [])]

    @staticmethod
    async def get_agent(db: AsyncSession, agent_id: str) -> Optional[Agent]:
        result = await db.execute(select(Agent).where(Agent.id == agent_id))
        return result.scalar_one_or_none()
