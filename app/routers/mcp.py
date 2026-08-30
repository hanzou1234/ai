import json
from typing import Any
from urllib.parse import urlparse

from fastapi import APIRouter
from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings

from app.config import settings
from app.database import AsyncSessionLocal
from app.services.escrow import P2PPaymentService
from app.services.negotiation import NegotiationService
from app.services.registry import RegistryService

router = APIRouter(prefix="/mcp", tags=["MCP"])

mcp_server = MCPServer(
    name="agent-economy-engine",
    title="Agent Economy Engine",
    description=(
        "Discover AI agents and negotiate signed skill contracts. "
        "Buyer-seller settlement is outside the platform."
    ),
    version="1.2.0",
)

base_url = urlparse(settings.BASE_URL)
transport_security = TransportSecuritySettings(
    allowed_hosts=[base_url.netloc, "localhost", "127.0.0.1"],
    allowed_origins=[settings.BASE_URL],
)


def _serialize_model(obj: Any) -> Any:
    if hasattr(obj, "__dict__"):
        return {
            key: value
            for key, value in obj.__dict__.items()
            if not key.startswith("_")
        }
    return obj


def _json_compatible(obj: Any) -> Any:
    return json.loads(json.dumps(obj, default=str))


@mcp_server.tool(description="Find agents by one or more capability tags, price, and sort order.")
async def search_agents(
    tags: list[str],
    max_price: float | None = None,
    sort_by: str = "price_asc",
    limit: int = 20,
) -> list[dict[str, Any]]:
    async with AsyncSessionLocal() as db:
        agents = await RegistryService.find_agents(
            db,
            tags=tags,
            max_price=max_price,
            sort_by=sort_by,
            limit=limit,
        )
        return _json_compatible([_serialize_model(agent) for agent in agents])


@mcp_server.tool(description="List all registered agents.")
async def list_agents() -> list[dict[str, Any]]:
    async with AsyncSessionLocal() as db:
        agents = await RegistryService.list_agents(db)
        return _json_compatible([_serialize_model(agent) for agent in agents])


@mcp_server.tool(description="Fetch an individual agent by ID.")
async def get_agent(agent_id: str) -> dict[str, Any]:
    async with AsyncSessionLocal() as db:
        agent = await RegistryService.get_agent(db, agent_id)
        if agent is None:
            raise ValueError(f"Agent not found: {agent_id}")
        return _json_compatible(_serialize_model(agent))


@mcp_server.tool(description="Register an AI agent with a public key and base price.")
async def register_agent(
    id: str,
    name: str,
    capabilities: dict[str, Any],
    base_price: float,
    signing_public_key: str,
    supervisor_public_key: str | None = None,
) -> dict[str, Any]:
    async with AsyncSessionLocal() as db:
        agent = await RegistryService.register_agent(
            db,
            id,
            name,
            capabilities,
            base_price,
            signing_public_key,
            supervisor_public_key,
        )
        return _json_compatible(_serialize_model(agent))


@mcp_server.tool(description="Create a signed contract proposal between buyer and seller agents.")
async def negotiate_contract(
    buyer_id: str,
    seller_id: str,
    task: str,
    offered_price: float,
    buyer_signature: str,
) -> dict[str, Any]:
    async with AsyncSessionLocal() as db:
        contract = await NegotiationService.propose_contract(
            db,
            buyer_id,
            seller_id,
            task,
            offered_price,
            buyer_signature,
        )
        return _json_compatible(_serialize_model(contract))


@mcp_server.tool(description="Accept a contract proposal with the seller signature.")
async def accept_contract(contract_id: str, seller_signature: str) -> dict[str, Any]:
    async with AsyncSessionLocal() as db:
        contract = await NegotiationService.accept_proposal(db, contract_id, seller_signature)
        return _json_compatible(_serialize_model(contract))


@mcp_server.tool(description="Approve a high-value contract using a party's supervisor signature.")
async def approve_contract(
    contract_id: str,
    agent_id: str,
    signature: str,
) -> dict[str, Any]:
    async with AsyncSessionLocal() as db:
        contract = await NegotiationService.approve_by_supervisor(
            db, contract_id, agent_id, signature
        )
        return _json_compatible(_serialize_model(contract))


@mcp_server.tool(description="Attest that an executing contract is complete using a party signature.")
async def attest_completion(
    contract_id: str,
    agent_id: str,
    signature: str,
) -> dict[str, Any]:
    async with AsyncSessionLocal() as db:
        contract = await NegotiationService.attest_completion(
            db, contract_id, agent_id, signature
        )
        return _json_compatible(_serialize_model(contract))


@mcp_server.tool(description="Create a Stripe Checkout URL for the platform fee after both parties attest completion.")
async def create_fee_checkout(contract_id: str) -> dict[str, Any]:
    async with AsyncSessionLocal() as db:
        payment = await P2PPaymentService.create_platform_fee_checkout(db, contract_id)
        return _json_compatible(payment)


@router.get("/health")
async def healthcheck():
    return {"status": "ok", "service": "agent-marketplace-mcp", "transport": "streamable-http"}


mcp_app = mcp_server.streamable_http_app(
    streamable_http_path="/",
    stateless_http=True,
    json_response=True,
    transport_security=transport_security,
)
