import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.negotiation import NegotiationService
from app.services.registry import RegistryService

router = APIRouter(prefix="/mcp", tags=["MCP"])


class JsonRpcRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: str | int | None = None
    method: str
    params: dict[str, Any] | None = None


MCP_TOOLS = [
    {
        "name": "search_agents",
        "description": "Find agents by capability tag.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "capability": {"type": "string", "description": "Capability tag such as research or writing."}
            },
            "required": ["capability"],
        },
    },
    {
        "name": "list_agents",
        "description": "List all registered agents.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_agent",
        "description": "Fetch an individual agent by ID.",
        "inputSchema": {
            "type": "object",
            "properties": {"agent_id": {"type": "string"}},
            "required": ["agent_id"],
        },
    },
    {
        "name": "register_agent",
        "description": "Register a new AI agent with a public key and base price.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "name": {"type": "string"},
                "capabilities": {"type": "object"},
                "base_price": {"type": "number"},
                "signing_public_key": {"type": "string"},
                "supervisor_public_key": {"type": ["string", "null"]},
            },
            "required": ["id", "name", "capabilities", "base_price", "signing_public_key"],
        },
    },
    {
        "name": "negotiate_contract",
        "description": "Create a signed contract proposal between a buyer and seller agent.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "buyer_id": {"type": "string"},
                "seller_id": {"type": "string"},
                "task": {"type": "string"},
                "offered_price": {"type": "number"},
                "buyer_signature": {"type": "string"},
            },
            "required": ["buyer_id", "seller_id", "task", "offered_price", "buyer_signature"],
        },
    },
    {
        "name": "accept_contract",
        "description": "Seller accepts a contract proposal by signing the acceptance payload.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "contract_id": {"type": "string"},
                "seller_signature": {"type": "string"},
            },
            "required": ["contract_id", "seller_signature"],
        },
    },
]


def _serialize_model(obj: Any) -> Any:
    if hasattr(obj, "__dict__"):
        base = {}
        for key, value in obj.__dict__.items():
            if key.startswith("_"):
                continue
            base[key] = value
        return base
    return obj


async def _execute_tool(tool_name: str, arguments: dict[str, Any], db: AsyncSession) -> Any:
    if tool_name == "search_agents":
        agents = await RegistryService.find_agents(db, arguments["capability"])
        return [_serialize_model(agent) for agent in agents]

    if tool_name == "list_agents":
        agents = await RegistryService.list_agents(db)
        return [_serialize_model(agent) for agent in agents]

    if tool_name == "get_agent":
        agent = await RegistryService.get_agent(db, arguments["agent_id"])
        if agent is None:
            raise ValueError(f"Agent not found: {arguments['agent_id']}")
        return _serialize_model(agent)

    if tool_name == "register_agent":
        agent = await RegistryService.register_agent(
            db,
            arguments["id"],
            arguments["name"],
            arguments.get("capabilities", {}),
            arguments["base_price"],
            arguments.get("signing_public_key"),
            arguments.get("supervisor_public_key"),
        )
        return _serialize_model(agent)

    if tool_name == "negotiate_contract":
        contract = await NegotiationService.propose_contract(
            db,
            arguments["buyer_id"],
            arguments["seller_id"],
            arguments["task"],
            arguments["offered_price"],
            arguments["buyer_signature"],
        )
        return _serialize_model(contract)

    if tool_name == "accept_contract":
        contract = await NegotiationService.accept_proposal(
            db,
            arguments["contract_id"],
            arguments["seller_signature"],
        )
        return _serialize_model(contract)

    raise ValueError(f"Unsupported tool: {tool_name}")


@router.get("/health")
async def healthcheck():
    return {"status": "ok", "service": "agent-marketplace-mcp"}


@router.post("")
async def handle_mcp(request: JsonRpcRequest, db: AsyncSession = Depends(get_db)):
    if request.method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": request.id,
            "result": {"tools": MCP_TOOLS},
        }

    if request.method == "tools/call":
        tool_name = (request.params or {}).get("name")
        tool_arguments = (request.params or {}).get("arguments", {}) or {}
        if not tool_name:
            raise HTTPException(status_code=400, detail="Tool name is required")
        try:
            result = await _execute_tool(tool_name, tool_arguments, db)
        except ValueError as exc:
            return {
                "jsonrpc": "2.0",
                "id": request.id,
                "error": {"code": -32000, "message": str(exc)},
            }

        payload = {
            "jsonrpc": "2.0",
            "id": request.id,
            "result": {
                "content": [{"type": "text", "text": json.dumps(result, default=str, ensure_ascii=False)}],
                "structuredContent": result,
            },
        }
        return payload

    if request.method == "ping":
        return {"jsonrpc": "2.0", "id": request.id, "result": {"status": "ok"}}

    return {
        "jsonrpc": "2.0",
        "id": request.id,
        "error": {"code": -32601, "message": f"Method not found: {request.method}"},
    }
