# P2P Payment Flow Documentation

## アーキテクチャ変更：エスクロー型 → P2P直接決済型

### 旧仕組み（エスクロー型）
```
バイヤー $100
    ↓
[プラットフォーム エスクロー]  ← リスク負担
    ↓
セラー $95 + プラットフォーム $5手数料
```

**問題点：** プラットフォームが資金管理責任を負う、チャージバック・不払いリスク

---

### 新仕組み（P2P直接決済型）✅
```
1. 契約作成
   バイヤー ↔ セラー（金額・条件に同意）

2. 支払いリンク生成
   /payments/create-payment-link/{contract_id}
   → Stripe Payment Link / PayPal Invoice を返却

3. バイヤーがセラーに直接支払い
   バイヤー → [Stripe / PayPal / Solana] → セラー
   （プラットフォームを経由しない）

4. 支払い完了報告
   /payments/complete-payment
   → プラットフォームがセラーのウォレットから手数料を自動徴収

5. 取引完了
   セラーはウォレットから手数料を支払うだけ
```

---

## リスク分散

| リスク | 責任 |
|--------|------|
| チャージバック | バイヤー・セラー（Stripe/PayPalの紛争解決機能） |
| 不払い | セラー（Stripeの支払い完了確認後に取引をロック） |
| プラットフォーム破産 | なし（手数料だけ徴収） |

**プラットフォームのリスク = ほぼゼロ** ✅

---

## API フロー

### 1. ネゴシエーション
```bash
POST /payments/negotiate
{
  "buyer_id": "buyer-001",
  "seller_id": "seller-001",
  "task": "Image processing",
  "offered_price": 100.0
}
```

**応答：** 契約ID取得

---

### 2. 支払いリンク生成
```bash
GET /payments/create-payment-link/{contract_id}
```

**応答：** バイヤー向けの支払いリンク
```json
{
  "payment_link": {
    "contract_id": "...",
    "seller_id": "...",
    "amount": 100.0,
    "currency": "USD"
  },
  "message": "バイヤーはセラーに直接支払ってください"
}
```

---

### 3. 支払い完了（セラーがAPI呼び出し）
```bash
POST /payments/complete-payment
{
  "contract_id": "..."
}
```

**処理内容：**
- Stripe/PayPalから支払い完了を確認
- セラーのウォレットから手数料を自動徴収
- 取引をCOMPLETEDにマーク

**応答：**
```json
{
  "message": "Payment completed and platform fee collected",
  "transaction": {
    "id": "...",
    "contract_id": "...",
    "gross_amount": 100.0,
    "platform_fee": 5.0,
    "seller_net_payout": 0.0,  ← P2Pなので0（セラーは直接受け取り）
    "type": "PLATFORM_FEE"
  }
}
```

---

### 4. 紛争報告（オプション）
```bash
POST /payments/report-dispute
{
  "contract_id": "...",
  "reason": "Seller did not deliver"
}
```

**処理内容：**
- プラットフォームは取引を FAILED にマーク
- バイヤー・セラーは Stripe/PayPal の紛争解決機能を使用

---

## セラーの手数料支払い方法

### 方法1：ウォレットから自動徴収（現在の実装）
```
セラーのウォレット残高 -= platform_fee
```

### 方法2：クレジットカードから定期徴収（推奨）
```python
# 月1回、セラーのクレジットカードから手数料まとめて徴収
async def charge_monthly_fees():
    # 先月の全取引から手数料を計算
    # セラーのクレジットカードに課金
    pass
```

---

## 本番化のチェックリスト

- [ ] Stripe Connect / PayPal Commerce Platform を統合
- [ ] 支払い完了の自動確認 webhook 実装
- [ ] セラー・バイヤーの KYC（本人確認）実装
- [ ] 手数料の月次レポート機能
- [ ] 紛争管理ダッシュボード
- [ ] PCI-DSS コンプライアンス確認

---

## まとめ

✅ **プラットフォームは手数料だけもらう仕組みに完全変更**
✅ **チャージバック・不払いのリスクはセラー・バイヤーが負担**
✅ **プラットフォームの責任最小化 = ビジネスリスク低減**
