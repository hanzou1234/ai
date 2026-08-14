import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.agent import Agent
from app.models.contract import Contract, ContractStatus
from app.models.transaction import Transaction
from app.config import settings

class P2PPaymentService:
    """P2P決済サービス：バイヤー↔セラー直接決済、プラットフォームは手数料のみ徴収"""

    @staticmethod
    async def create_payment_link(db: AsyncSession, contract_id: str):
        """セラー向けの支払いリンク生成（Stripe Invoiceなど）"""
        result = await db.execute(select(Contract).where(Contract.id == contract_id))
        contract = result.scalar_one_or_none()
        if not contract:
            raise ValueError("Contract not found")

        # バイヤーがセラーに直接支払うためのリンクを生成
        # 実装例：Stripe Payment Link, PayPal Invoice等
        payment_data = {
            "contract_id": contract_id,
            "seller_id": contract.seller_id,
            "buyer_id": contract.buyer_id,
            "amount": contract.agreed_price,
            "currency": "USD",
            "description": f"Task: {contract.task_description}"
        }
        return payment_data

    @staticmethod
    async def record_payment_completion(db: AsyncSession, contract_id: str):
        """支払い完了：セラーから手数料を徴収"""
        result = await db.execute(select(Contract).where(Contract.id == contract_id))
        contract = result.scalar_one_or_none()
        if not contract or contract.status != ContractStatus.EXECUTING:
            raise ValueError("Invalid contract state")

        gross_amount = contract.agreed_price
        fee_rate = settings.PLATFORM_FEE_RATE
        min_fee = settings.MINIMUM_PLATFORM_FEE
        
        # 手数料計算：最小手数料を適用
        calculated_fee = round(gross_amount * fee_rate, 2)
        platform_fee = max(calculated_fee, min_fee)

        # セラーから手数料を徴収（ウォレットから）
        seller_result = await db.execute(select(Agent).where(Agent.id == contract.seller_id))
        seller = seller_result.scalar_one()
        
        if seller.wallet_balance < platform_fee:
            raise ValueError("Seller insufficient balance for platform fee")
        
        seller.wallet_balance -= platform_fee

        # 取引記録：プラットフォーム手数料のみ
        tx = Transaction(
            id=str(uuid.uuid4()),
            contract_id=contract_id,
            gross_amount=gross_amount,
            platform_fee=platform_fee,
            seller_net_payout=0.0,  # P2P決済なので0（セラーは直接受け取り）
            type="PLATFORM_FEE"
        )
        db.add(tx)
        contract.status = ContractStatus.COMPLETED
        await db.commit()
        return tx

    @staticmethod
    async def refund_if_dispute(db: AsyncSession, contract_id: str, reason: str):
        """紛争時：セラー・バイヤーに対応を委譲（プラットフォームは関与しない）"""
        result = await db.execute(select(Contract).where(Contract.id == contract_id))
        contract = result.scalar_one_or_none()
        
        # プラットフォームは紛争解決に関与しない
        # セラー・バイヤーが Stripe/PayPal の紛争解決機能を使用
        contract.status = ContractStatus.FAILED
        await db.commit()
        
        return {
            "message": "Dispute reported. Please use payment provider's dispute resolution.",
            "contract_id": contract_id,
            "reason": reason
        }

