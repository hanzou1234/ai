import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.database import Base
from app.models.agent import Agent
from app.services.registry import RegistryService


@pytest.mark.asyncio
async def test_discovery_filters_multiple_tags_and_sorts_by_price(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'registry.db'}")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        session.add_all([
            Agent(id="research-low", name="Research Low", capabilities={"tags": ["research", "web"]}, base_price=5),
            Agent(id="research-high", name="Research High", capabilities={"tags": ["research", "web"]}, base_price=20),
            Agent(id="writing", name="Writer", capabilities={"tags": ["writing"]}, base_price=2),
        ])
        await session.commit()

        agents = await RegistryService.find_agents(
            session,
            tags=["research", "web"],
            max_price=10,
        )

    assert [agent.id for agent in agents] == ["research-low"]
    await engine.dispose()