import httpx
import asyncio
import logging

class BuyerAgent:
    def __init__(self, agent_id: str, base_url: str = "http://localhost:8000"):
        self.agent_id = agent_id
        self.base_url = base_url
        self.logger = logging.getLogger(f"BuyerAgent-{agent_id}")

    async def run_task_cycle(self, required_capability: str, task_desc: str, budget: float):
        async with httpx.AsyncClient() as client:
            # 1. Discovery
            self.logger.info(f"Searching for sellers with capability: {required_capability}")
            resp = await client.get(f"{self.base_url}/registry/search", params={"capability": required_capability})
            sellers = resp.json()
            if not sellers:
                self.logger.error("No sellers found")
                return

            # Pick the cheapest one
            best_seller = min(sellers, key=lambda x: x["base_price"])
            self.logger.info(f"Selected seller: {best_seller['name']} at {best_seller['base_price']}")

            # 2. Negotiation
            negotiate_data = {
                "buyer_id": self.agent_id,
                "seller_id": best_seller["id"],
                "task": task_desc,
                "offered_price": best_seller["base_price"]
            }
            resp = await client.post(f"{self.base_url}/escrow/negotiate", json=negotiate_data)
            contract = resp.json()
            contract_id = contract["id"]
            self.logger.info(f"Contract agreed: {contract_id}")

            # 3. Escrow Deposit
            resp = await client.post(f"{self.base_url}/escrow/deposit/{contract_id}")
            self.logger.info(f"Escrow deposited for contract {contract_id}")

            return contract_id

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    buyer = BuyerAgent("buyer-001")
    # This would normally be called in an event loop
