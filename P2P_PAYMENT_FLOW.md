# P2P Payment Flow Documentation

## Architecture change: escrow model → direct P2P settlement

### Old model (escrow-based)
```
Buyer $100
    ↓
[Platform escrow]  ← risk borne by platform
    ↓
Seller $95 + platform fee $5
```

**Problem:** the platform assumes custody and operational responsibility for funds, creating chargeback and non-payment risk.

---

### New model (direct P2P settlement) ✅
```
1. Contract creation
   Buyer ↔ Seller (agree on amount and conditions)

2. Payment link generation
   /payments/create-payment-link/{contract_id}
   → returns a Stripe Payment Link / PayPal Invoice

3. Buyer pays the seller directly
   Buyer → [Stripe / PayPal / Solana] → Seller
   (without routing funds through the platform)

4. Payment completion report
   /payments/complete-payment
   → the platform automatically collects the fee from the seller wallet

5. Transaction complete
   The seller only pays the platform fee from the wallet balance
```

---

## Risk allocation

| Risk | Responsibility |
|------|---------------|
| Chargebacks | Buyer and seller (via Stripe/PayPal dispute mechanisms) |
| Non-payment | Seller (transaction is locked after payment confirmation by Stripe) |
| Platform insolvency | None (platform collects only fees) |

**Platform risk = nearly zero** ✅

---

## API flow

### 1. Negotiation
```bash
POST /payments/negotiate
{
  "buyer_id": "buyer-001",
  "seller_id": "seller-001",
  "task": "Image processing",
  "offered_price": 100.0
}
```

**Response:** contract ID is returned.

---

### 2. Payment link generation
```bash
GET /payments/create-payment-link/{contract_id}
```

**Response:** buyer-facing payment link
```json
{
  "payment_link": {
    "contract_id": "...",
    "seller_id": "...",
    "amount": 100.0,
    "currency": "USD"
  },
  "message": "The buyer should pay the seller directly"
}
```

---

### 3. Payment completed (seller calls the API)
```bash
POST /payments/complete-payment
{
  "contract_id": "..."
}
```

**Processing:**
- confirm payment completion from Stripe/PayPal
- automatically collect the platform fee from the seller wallet
- mark the transaction as COMPLETED

**Response:**
```json
{
  "message": "Payment completed and platform fee collected",
  "transaction": {
    "id": "...",
    "contract_id": "...",
    "gross_amount": 100.0,
    "platform_fee": 5.0,
    "seller_net_payout": 0.0,  // P2P means 0 because the seller is paid directly
    "type": "PLATFORM_FEE"
  }
}
```

---

### 4. Dispute reporting (optional)
```bash
POST /payments/report-dispute
{
  "contract_id": "...",
  "reason": "Seller did not deliver"
}
```

**Processing:**
- the platform marks the transaction as FAILED
- buyer and seller handle dispute resolution through Stripe/PayPal mechanisms

---

## Seller fee payment methods

### Method 1: automatic deduction from wallet (current implementation)
```
Seller wallet balance -= platform_fee
```

### Method 2: recurring charge from credit card (recommended)
```python
# Charge the seller's credit card once per month for cumulative fees
async def charge_monthly_fees():
    # calculate total fees from all transactions in the previous month
    # charge the seller's credit card
    pass
```

---

## Production readiness checklist

- [ ] Integrate Stripe Connect / PayPal Commerce Platform
- [ ] Implement automatic payment confirmation webhooks
- [ ] Implement KYC for buyers and sellers
- [ ] Add monthly fee reporting
- [ ] Add a dispute management dashboard
- [ ] Confirm PCI-DSS compliance

---

## Summary

✅ **The platform has been redesigned to collect only a transaction fee**
✅ **Chargeback and non-payment risk is borne by buyer and seller**
✅ **Minimizing platform responsibility = lower business risk**
