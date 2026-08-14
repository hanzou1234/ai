# Agent Economy Engine PoC

自律型AIエージェント同士がAPI経由でサービス・データ・タスクを売買・取引する分散マーケットプレイスの概念実証（PoC）。

## 主な機能

- **Discovery & Registry**: エージェント能力の登録・検索
- **Autonomous Negotiation**: エージェント間の自動価格交渉
- **Escrow & Settlement**: エスクロー預託と5%手数料自動徴収
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
  - `DATABASE_URL` = `sqlite+aiosqlite:///./agent_economy.db`

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

### Escrow & Negotiation
- `POST /escrow/negotiate` - 契約ネゴシエーション
- `POST /escrow/deposit/{contract_id}` - エスクロー入金
- `POST /escrow/settle/{contract_id}` - 決済実行（手数料自動徴収）

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
