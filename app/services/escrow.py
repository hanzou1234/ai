import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.contract import Contract, ContractStatus
from app.models.transaction import Transaction
from app.services.payment_stripe import StripePaymentService

class P2PPaymentService:
    """P2P決済サービス：バイヤー↔セラー直接決済、プラットフォームは手数料のみ徴収"""

    @staticmethod
    async def create_platform_fee_checkout(db: AsyncSession, contract_id: str):
        """売買代金には触れず、プラットフォーム手数料だけを請求する。"""
        result = await db.execute(select(Contract).where(Contract.id == contract_id))
        contract = result.scalar_one_or_none()
        if not contract:
            raise ValueError("Contract not found")

        if contract.status not in (ContractStatus.ESCROWED, ContractStatus.EXECUTING):
            raise ValueError("Fee checkout is available after contract acceptance")

        session = await StripePaymentService.create_platform_fee_checkout(
            contract.id, contract.seller_id, contract.agreed_price
        )
        return {
            "checkout_url": session.url,
            "checkout_session_id": session.id,
            "platform_fee": StripePaymentService.calculate_platform_fee(contract.agreed_price),
            "currency": "USD",
            "buyer_seller_payment": "outside_platform",
        }

    @staticmethod
    async def record_platform_fee_payment(db: AsyncSession, contract_id: str, session_id: str, amount: float):
        """Stripe webhookでプラットフォーム手数料の支払いだけを記録する。"""
        result = await db.execute(select(Contract).where(Contract.id == contract_id))
        contract = result.scalar_one_or_none()
        if not contract:
            raise ValueError("Invalid contract state")

        existing = await db.get(Transaction, session_id)
        if existing:
            return existing

        tx = Transaction(
            id=session_id,
            contract_id=contract_id,
            gross_amount=contract.agreed_price,
            platform_fee=amount,
            seller_net_payout=0.0,  # P2P決済なので0（セラーは直接受け取り）
            type="PLATFORM_FEE_STRIPE"
        )
        db.add(tx)
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

