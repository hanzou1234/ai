import stripe
from app.config import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

class StripePaymentService:
    @staticmethod
    async def create_payment_intent(buyer_id: str, amount: float):
        """バイヤーの支払いインテント作成"""
        intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),  # セント単位
            currency="usd",
            customer=buyer_id,
            description="Agent Economy Platform Transaction"
        )
        return intent

    @staticmethod
    async def process_seller_payout(seller_id: str, amount: float):
        """セラーへの自動送金"""
        transfer = stripe.Transfer.create(
            amount=int(amount * 100),
            currency="usd",
            destination=seller_id,
            description="Settlement payout for completed task"
        )
        return transfer

    @staticmethod
    async def charge_buyer(payment_intent_id: str):
        """バイヤーに課金実行"""
        intent = stripe.PaymentIntent.confirm(payment_intent_id)
        return intent.status == "succeeded"
