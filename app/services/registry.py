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
    async def find_agents(
        db: AsyncSession,
        capability: str | None = None,
        tags: list[str] | None = None,
        max_price: float | None = None,
        sort_by: str = "price_asc",
        limit: int = 20,
    ) -> List[Agent]:
        result = await db.execute(select(Agent))
        agents = result.scalars().all()
        requested_tags = {tag.strip().lower() for tag in tags or [] if tag.strip()}
        if capability:
            requested_tags.add(capability.strip().lower())

        if requested_tags:
            agents = [
                agent
                for agent in agents
                if requested_tags.issubset(
                    {tag.lower() for tag in agent.capabilities.get("tags", [])}
                )
            ]
        if max_price is not None:
            agents = [agent for agent in agents if agent.base_price <= max_price]

        if sort_by == "name_asc":
            agents.sort(key=lambda agent: (agent.name.lower(), agent.base_price))
        else:
            agents.sort(key=lambda agent: (agent.base_price, agent.name.lower()))
        return agents[:max(1, min(limit, 100))]

    @staticmethod
    async def list_agents(db: AsyncSession) -> List[Agent]:
        result = await db.execute(select(Agent).order_by(Agent.name))
        return result.scalars().all()

    @staticmethod
    async def get_agent(db: AsyncSession, agent_id: str) -> Optional[Agent]:
        result = await db.execute(select(Agent).where(Agent.id == agent_id))
        return result.scalar_one_or_none()
