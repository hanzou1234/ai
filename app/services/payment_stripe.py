import stripe
from app.config import settings

stripe.api_key = settings.STRIPE_API_KEY

class StripePaymentService:
    @staticmethod
    def calculate_platform_fee(amount: float) -> float:
        calculated_fee = round(amount * settings.PLATFORM_FEE_RATE, 2)
        return max(calculated_fee, settings.MINIMUM_PLATFORM_FEE)

    @staticmethod
    async def create_platform_fee_checkout(contract_id: str, seller_id: str, amount: float):
        """Create a checkout session for the platform fee only.

        The buyer-seller payment happens outside this platform.
        """
        platform_fee = StripePaymentService.calculate_platform_fee(amount)
        return stripe.checkout.Session.create(
            mode="payment",
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {"name": "Agent Economy Engine platform fee"},
                    "unit_amount": int(round(platform_fee * 100)),
                },
                "quantity": 1,
            }],
            metadata={
                "type": "platform_fee",
                "contract_id": contract_id,
                "seller_id": seller_id,
            },
            success_url=f"{settings.BASE_URL}/payments/fee-success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.BASE_URL}/payments/fee-cancelled",
        )
