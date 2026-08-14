import httpx
import asyncio
import logging

class SellerAgent:
    def __init__(self, agent_id: str, name: str, base_url: str = "http://localhost:8000"):
        self.agent_id = agent_id
        self.name = name
        self.base_url = base_url
        self.logger = logging.getLogger(f"SellerAgent-{agent_id}")

    async def register(self, capabilities: list, price: float):
        async with httpx.AsyncClient() as client:
            data = {
                "id": self.agent_id,
                "name": self.name,
                "capabilities": {"tags": capabilities},
                "base_price": price
            }
            resp = await client.post(f"{self.base_url}/registry/register", json=data)
            self.logger.info(f"Registered as {self.name}: {resp.status_code}")

    async def complete_task(self, contract_id: str):
        async with httpx.AsyncClient() as client:
            # Simulate work
            self.logger.info(f"Executing task for contract {contract_id}...")
            await asyncio.sleep(1)
            
            # Request settlement
            resp = await client.post(f"{self.base_url}/escrow/settle/{contract_id}")
            self.logger.info(f"Task completed and settled: {resp.json()}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    seller = SellerAgent("seller-001", "GPT-4-Vision-Service")
