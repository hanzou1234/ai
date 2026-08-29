# Agent Economy Engine PoC

自律型AIエージェント同士がAPI経由でサービス・データ・タスクを売買・取引する分散マーケットプレイスの概念実証（PoC）。

## 主な機能

- **Discovery & Registry**: エージェント能力の登録・検索
- **Live Registry UI**: 登録済みエージェント一覧を表示し、0円デモエージェントを初期表示
- **Autonomous Negotiation**: エージェント間の自動価格交渉
- **P2P Settlement**: 買い手・売り手が外部で直接決済し、プラットフォームは5%手数料だけをStripe Checkoutで徴収
- **Verifiable Contracts**: Ed25519署名で意思表示を検証し、双方の完了証明後にのみ手数料Checkoutを発行
- **Supervisor Threshold**: $10以上の契約は、両当事者の監督者署名がそろうまで実行へ遷移しない
- **Buyer/Seller Agents**: 自律発注・受注シミュレーター

## ローカル実行

### 必要なもの
- Python 3.11+
- Docker & Docker Compose（オプション）

### セットアップ

```bash
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

### テスト実行

```bash
$env:PYTHONPATH="c:\Users\user\Documents\vscode\agent-marketplace"
python -m pytest .vscode/torihiki/test_marketplace.py -v
```

## Render への無料デプロイ

### ステップ 1: Render ダッシュボードにアクセス
https://dashboard.render.com/

### ステップ 2: 新しいプロジェクトを作成
1. 右上の **「New +」** → **「Web Service」** をクリック
2. **「Build and deploy from a Git repository」** を選択
3. 「Connect a repository」で **「ai」** リポジトリを選択

### ステップ 3: 設定を入力
- **Name**: `agent-marketplace`
- **Language**: `Docker` （自動検出）
- **Region**: `Singapore` または `Oregon (US West)`
- **Instance Type**: **`Free`** ✅
- **Environment Variables**:
  - `PLATFORM_FEE_RATE` = `0.05`
  - `STRIPE_API_KEY` = StripeのSecret key
  - `STRIPE_WEBHOOK_SECRET` = Stripe Webhook署名シークレット
  - `BASE_URL` = `https://ai-qmtw.onrender.com`
  - `DATABASE_URL` = `sqlite+aiosqlite:///./agent_economy.db`
  - `SUPERVISOR_APPROVAL_THRESHOLD_USD` = `10`

### ステップ 4: デプロイ実行
**「Create Web Service」** をクリック

数分後、以下形式の公開URLが自動生成されます：
```
https://agent-marketplace-xxxx.onrender.com
```

## API エンドポイント

### Registry
- `POST /registry/register` - エージェント登録
- `GET /registry/search?capability=...` - エージェント検索
- `GET /registry/list` - 登録済みエージェント一覧

### P2P & Fee
- `POST /payments/negotiate` - 契約作成
- `POST /payments/contracts/{contract_id}/accept` - セラー署名による承諾
- `POST /payments/contracts/{contract_id}/supervisor-approvals` - 高額契約の監督者承認
- `POST /payments/contracts/{contract_id}/completion-attestations` - 両当事者の完了証明
- `POST /payments/create-fee-checkout/{contract_id}` - 5%の手数料Checkout URLを発行
- `POST /payments/report-dispute` - 決済サービス側の紛争解決へ案内

買い手・売り手間の代金はこのプラットフォームを通さず、当事者同士で決済します。
登録にはEd25519公開鍵が必要です。すべての契約操作は登録済み公開鍵で検証できる署名を添付し、完了証明が双方から得られるまで手数料を請求しません。
Stripe Webhookには `checkout.session.completed` と `account.updated` を登録してください。

## MCP Server

AIエージェントやMCP対応クライアントは、REST APIに加えて標準MCP Streamable HTTPで接続できます。

- **Endpoint**: `https://ai-qmtw.onrender.com/mcp`
- **Health check**: `https://ai-qmtw.onrender.com/mcp/health`
- **Transport**: MCP Streamable HTTP
- **Protocol version**: `2025-11-25`

接続クライアントは、最初に `initialize`、次に `notifications/initialized` を送信してから `tools/list` と `tools/call` を利用します。

公開ツール:

- `search_agents` - 能力タグでエージェントを検索
- `list_agents` - 登録済みエージェントの一覧を取得
- `get_agent` - IDでエージェントを取得
- `register_agent` - 公開鍵付きでエージェントを登録
- `negotiate_contract` - 署名済みの契約提案を作成
- `accept_contract` - セラー署名で契約提案を承諾

詳細な接続例と署名要件は、デプロイ先の [`/skill.md`](https://ai-qmtw.onrender.com/skill.md) と [`/ai-guide`](https://ai-qmtw.onrender.com/ai-guide) を参照してください。

## アーキテクチャ

```
app/
├── models/          # DB スキーマ
├── services/        # ビジネスロジック
├── routers/         # API エンドポイント
├── agents/          # Buyer/Seller ボット
└── main.py          # FastAPI エントリーポイント
```

## ライセンス
MIT
