from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.registry import RegistryService
from pydantic import BaseModel
from typing import List, Dict

router = APIRouter(prefix="/registry", tags=["Registry"])

class AgentCreate(BaseModel):
    id: str
    name: str
    capabilities: Dict
    base_price: float

@router.post("/register")
async def register(agent_data: AgentCreate, db: AsyncSession = Depends(get_db)):
    return await RegistryService.register_agent(
        db, agent_data.id, agent_data.name, agent_data.capabilities, agent_data.base_price
    )

@router.get("/search")
async def search(capability: str, db: AsyncSession = Depends(get_db)):
    return await RegistryService.find_agents(db, capability)
