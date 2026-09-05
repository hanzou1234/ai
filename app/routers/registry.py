from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.registry import RegistryService
from pydantic import BaseModel
from typing import Any, Dict, Literal

router = APIRouter(prefix="/registry", tags=["Registry"])

class AgentCreate(BaseModel):
    id: str
    name: str
    capabilities: Dict[str, Any]
    description: str | None = None
    base_price: float
    signing_public_key: str
    supervisor_public_key: str | None = None

    def normalize_capabilities(self) -> Dict[str, Any]:
        normalized = dict(self.capabilities)
        if self.description and not normalized.get("description"):
            normalized["description"] = self.description
        return normalized

@router.post("/register")
async def register(agent_data: AgentCreate, db: AsyncSession = Depends(get_db)):
    capabilities = agent_data.normalize_capabilities()
    return await RegistryService.register_agent(
        db,
        agent_data.id,
        agent_data.name,
        capabilities,
        agent_data.base_price,
        agent_data.signing_public_key,
        agent_data.supervisor_public_key,
    )

@router.get("/search")
async def search(
    capability: str | None = None,
    tags: str | None = None,
    query: str | None = None,
    max_price: float | None = None,
    sort_by: Literal["price_asc", "name_asc"] = "price_asc",
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    requested_tags = tags.split(",") if tags else None
    return await RegistryService.find_agents(
        db,
        capability=capability,
        tags=requested_tags,
        query=query,
        max_price=max_price,
        sort_by=sort_by,
        limit=limit,
        offset=offset,
    )

@router.get("/list")
async def list_agents(limit: int = 20, offset: int = 0, db: AsyncSession = Depends(get_db)):
    return await RegistryService.list_agents(db, limit=limit, offset=offset)
