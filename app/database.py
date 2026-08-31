from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import inspect, text
from app.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

def add_security_columns(sync_connection):
    columns_by_table = {
        "agents": {
            "signing_public_key": "VARCHAR",
            "supervisor_public_key": "VARCHAR",
        },
        "contracts": {
            "buyer_signature": "VARCHAR",
            "seller_signature": "VARCHAR",
            "buyer_supervisor_signature": "VARCHAR",
            "seller_supervisor_signature": "VARCHAR",
            "buyer_completion_signature": "VARCHAR",
            "seller_completion_signature": "VARCHAR",
        },
    }
    inspector = inspect(sync_connection)
    for table_name, columns in columns_by_table.items():
        existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
        for column_name, column_type in columns.items():
            if column_name not in existing_columns:
                sync_connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"))

async def init_db():
    from app.models.agent import Agent

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(add_security_columns)
    async with AsyncSessionLocal() as session:
        sample = await session.get(Agent, "demo-free-agent")
        if not sample:
            session.add(Agent(
                id="demo-free-agent",
                name="Free Demo Agent",
                capabilities={
                    "tags": ["demo", "research", "free"],
                    "description": "Provides free research and topic summaries for demo onboarding.",
                },
                base_price=0.0,
                signing_public_key="AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=",
            ))
            await session.commit()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
