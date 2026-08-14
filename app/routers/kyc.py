from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import stripe

from app.database import get_db
from app.config import settings
from app.services.kyc import KYCService
from app.models.kyc import KYCRecord, KYCRecordSchema, KYCStatus # KYCRecordSchemaとKYCStatusをインポート

router = APIRouter()
stripe.api_key = settings.STRIPE_API_KEY

@router.post("/kyc/start/{agent_id}", response_model=str) # リダイレクトURLを返すためstr
async def start_kyc_onboarding(agent_id: str, db: AsyncSession = Depends(get_db)):
    """
    Initiate KYC onboarding for an agent by creating a Stripe Connect account and a return URL.
    Returns the Stripe Account Link URL to redirect the agent to.
    """
    kyc_service = KYCService(db)
    existing_kyc = await kyc_service.get_kyc_record(agent_id)

    if existing_kyc and existing_kyc.stripe_connected_account_id:
        # 既存のConnectアカウントがあれば、再度Account Linkを生成
        account = stripe.Account.retrieve(existing_kyc.stripe_connected_account_id)
        if account.capabilities.card_payments.status == 'active' and account.capabilities.transfers.status == 'active':
            # 既に全てが有効なら、再度オンボーディングは不要かもしれないが、念のためAccount Linkを生成して確認させる
            print(f"Agent {agent_id} already has active Stripe Connect account {existing_kyc.stripe_connected_account_id}")
            pass # 後続でAccount Link生成
        elif not account.details_submitted:
            # 情報が未提出ならオンボーディングを継続
            print(f"Agent {agent_id} Connect account {existing_kyc.stripe_connected_account_id} details not submitted.")
            pass # 後続でAccount Link生成
        else:
            # その他の状態（審査中など）
            print(f"Agent {agent_id} Connect account {existing_kyc.stripe_connected_account_id} status: {account.capabilities.card_payments.status}, {account.capabilities.transfers.status}")
            # エラーではなく、現在のKYCステータスを返すなど、より詳細なハンドリングが必要
            # 今回は、常にオンボーディングリンクを生成する
            pass

    else:
        # Connectアカウントがなければ新規作成
        account = stripe.Account.create(
            type='express',
            country='JP', # 日本の事業者として登録
            email=f"agent_{agent_id}@example.com", # 仮のメールアドレス、後でエージェント情報から取得
            capabilities={
                'card_payments': {'requested': True},
                'transfers': {'requested': True},
            },
            metadata={'user_id': agent_id} # プラットフォームのuser_idをStripeのmetadataに保存
        )
        print(f"Created new Stripe Connect account: {account.id} for agent {agent_id}")
        
        # KYCレコードを更新（Stripe ConnectアカウントIDを紐付け）
        await kyc_service.create_kyc_record_for_agent(agent_id) # 既存のKYCレコードがなければ作成
        await kyc_service.update_stripe_account(
            user_id=agent_id, 
            stripe_connected_account_id=account.id
        )
        
    # Account Linkを生成して、エージェントをStripeのオンボーディングにリダイレクト
    account_link = stripe.AccountLink.create(
        account=account.id,
        refresh_url=f"https://ai-qmtw.onrender.com/kyc/start/{agent_id}", # リンク切れの際に再生成するためのURL
        return_url=f"https://ai-qmtw.onrender.com/kyc/complete/{agent_id}", # オンボーディング完了後のリダイレクト先
        type='account_onboarding',
    )
    
    return account_link.url

@router.get("/kyc/complete/{agent_id}")
async def kyc_complete(agent_id: str, db: AsyncSession = Depends(get_db)):
    """
    Return URL after Stripe onboarding.
    Agent will be redirected here after completing (or skipping) Stripe's onboarding flow.
    """
    kyc_service = KYCService(db)
    kyc_record = await kyc_service.get_kyc_record(agent_id)

    if not kyc_record:
        raise HTTPException(status_code=404, detail="KYC record not found.")

    # ここでStripe Connectアカウントの最新の状態をフェッチして、KYCレコードを更新することもできる
    # Webhookが最終的な更新を行うため、ここではユーザーにメッセージを表示するだけでも良い
    
    # 実際には、フロントエンドにリダイレクトしてステータスを表示すべき
    return {"message": f"KYC onboarding for agent {agent_id} complete. Please check your KYC status."}

@router.get("/kyc/status/{agent_id}", response_model=KYCRecordSchema)
async def get_kyc_status(agent_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve current KYC status for an agent."""
    kyc_service = KYCService(db)
    kyc_record = await kyc_service.get_kyc_record(agent_id)
    if not kyc_record:
        raise HTTPException(status_code=404, detail="KYC record not found.")
    return kyc_record