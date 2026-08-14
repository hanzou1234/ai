from fastapi import APIRouter, Request, Header, HTTPException
import stripe
from app.config import settings
from app.services.kyc import KYCService # KYCServiceをインポート
from app.database import AsyncSessionLocal # session_factoryをインポート

router = APIRouter()
stripe.api_key = settings.STRIPE_API_KEY

@router.post("/webhook")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None)):
    payload = await request.body()
    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, settings.STRIPE_WEBHOOK_SECRET
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # ここでイベントを処理（KYC完了時など）
    if event['type'] == 'account.updated':
        account = event['data']['object']
        
        # Stripe Connectアカウントのmetadataからuser_idを取得
        # Connectアカウント作成時にmetadataにuser_idを含めている前提
        user_id = account.get('metadata', {}).get('user_id')
        if not user_id:
            print(f"Warning: user_id not found in metadata for Stripe account {account['id']}")
            return {"status": "skipped", "reason": "user_id missing"}
        
        user_id = int(user_id) # metadataは文字列なので整数に変換

        # Stripeのverification.statusをKYCStatusに変換
        # details_submitted: アカウントの情報が提出されたか
        # charges_enabled: 決済を受け付ける準備ができているか（＝KYCが完了している目安）
        if account.get('details_submitted') and account.get('charges_enabled'):
            kyc_status_str = "VERIFIED"
        elif account.get('details_submitted') and not account.get('charges_enabled'):
            kyc_status_str = "UNDER_REVIEW" # 情報提出済みだが、まだ決済有効になっていない
        else:
            kyc_status_str = "PENDING" # 情報がまだ提出されていない
            
        async with AsyncSessionLocal() as session:
            kyc_service = KYCService(session)
            await kyc_service.verify_from_stripe(
                user_id=user_id, 
                stripe_status=kyc_status_str,
                stripe_connected_account_id=account['id']
            )
        print(f"Account updated: {account['id']}, user_id: {user_id}, KYC Status: {kyc_status_str}")
    elif event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        print(f"PaymentIntent succeeded: {payment_intent['id']}")
    
    return {"status": "success"}