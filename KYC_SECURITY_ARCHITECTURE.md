## KYC Security Architecture - Platform Zero-Liability Design

### 🎯 Objective
**Eliminate platform liability for identity document breaches**

### ❌ What We DON'T Do
- ❌ Store identity documents
- ❌ Collect scans of passports/driver's licenses
- ❌ Upload documents to our servers
- ❌ Process government ID numbers
- ❌ Handle biometric data

### ✅ What We DO Do
- ✅ Delegate KYC to Stripe Connect
- ✅ Store Stripe Connected Account ID (reference only)
- ✅ Track verification status from Stripe
- ✅ Handle AML flags from Stripe
- ✅ Reference Stripe privacy policy in our terms

---

## Architecture Flow

### Step 1: User Initiates KYC (in UI)
```
Agent Registration
    ↓
[Platform] "You need to verify with Stripe"
    ↓
User clicks: "Complete Verification"
    ↓
Redirect to: https://connect.stripe.com/onboarding/[link]
```

### Step 2: User Verifies with Stripe (NOT our servers)
```
[Stripe Hosted Form]
    ├─ Upload identity document
    ├─ Enter personal info
    ├─ Conduct sanctions screening
    └─ Process AML checks
    
All data stored in: Stripe's secure servers
```

### Step 3: Platform Receives Webhook (Stripe notifies us)
```
Stripe → Platform (webhook)
├─ Event: account.updated
├─ Status: verified / rejected / pending
├─ Stripe Account ID: acct_xxx
└─ (NO identity documents sent)
    ↓
[Platform] Stores: {user_id, stripe_account_id, status}
```

### Step 4: Future Transactions
```
Agent wants to transact
    ↓
[Platform checks] kyc_records.is_verified(user_id)
    ↓
If verified: ✅ Allow transaction
If rejected: ❌ Block transaction
```

---

## Risk Distribution

| Risk | Party | Handling |
|------|-------|----------|
| **Document Breach** | Stripe | Stripe's security & liability |
| **Fraud Detection** | Stripe | Stripe's AML system |
| **Sanctions Matching** | Stripe | Stripe's compliance team |
| **Document Expiry** | Stripe | Stripe sends update webhook |
| **Dispute with Stripe** | Stripe | User contacts Stripe support |
| **Platform Downtime** | Platform | Platform responsible |
| **Payment Processing Error** | Payment Provider | Provider responsible |
| **Fee Calculation Error** | Platform | Platform responsible |

**Result:** Platform bears ZERO liability for document security ✅

---

## Legal Compliance

### Terms of Service Section 3 (Payment Processing & KYC)
- ✅ Clarifies documents are NOT stored by Platform
- ✅ Directs users to Stripe for verification
- ✅ References Stripe's privacy policy
- ✅ States: "Document security is Stripe's responsibility"

### Privacy Policy Section 1 (Data We Do NOT Collect)
- ✅ Explicitly lists documents we DON'T collect
- ✅ Explains: "If documents are compromised, we don't bear liability"
- ✅ Minimal data storage = minimal risk

### AML Policy Section 1 (Sanctions & PEP Screening)
- ✅ States: "Stripe handles screening"
- ✅ Users cannot argue "Platform didn't verify"
- ✅ Compliance trail points to Stripe

---

## Implementation Checklist

### Database Model (app/models/kyc.py)
- ✅ KYCRecord stores ONLY:
  - user_id
  - stripe_connected_account_id (reference)
  - stripe_verification_status (from webhook)
  - verification_date
  - aml_flagged (if Stripe detects)

- ❌ Does NOT store:
  - document_type / document_number
  - document_front_url / document_back_url
  - personal address info
  - government ID numbers

### KYC Service (app/services/kyc.py)
- ✅ `create_kyc_record_for_agent()` - Creates empty record, ready for Stripe link
- ✅ `update_stripe_account()` - Called AFTER user returns from Stripe form
- ✅ `verify_from_stripe()` - Called when Stripe webhook arrives
- ✅ `flag_aml()` - Called if Stripe flags for AML

### Legal Routes (app/routers/legal.py)
- ✅ `GET /legal/terms` - Terms of Service
- ✅ `GET /legal/privacy` - Privacy Policy (updated: no docs stored)
- ✅ `GET /legal/aml-policy` - AML Policy (updated: Stripe handles)
- ✅ `GET /legal/disclaimer` - Disclaimer

---

## Next Steps (Phase 2)

### Implement Stripe Connect Integration
```
1. Create Stripe account (platform account)
2. Implement /kyc/start endpoint
   - Create KYC record in DB
   - Call Stripe API: create Account Link
   - Return onboarding_link to user
   
3. Implement /stripe/webhook endpoint
   - Receive account.updated events
   - Update KYC record with verification_status
   - Flag AML if needed
   
4. Implement /kyc/status endpoint
   - User checks: "Am I verified?"
   - Platform queries: kyc_records.is_verified(user_id)
```

### Webhook Verification
```
POST /stripe/webhook
  - Verify signature: Stripe-Signature header
  - Process: account.updated event
  - Call: KYCService.verify_from_stripe()
  - Response: 200 OK (or webhook retries)
```

---

## Security Guarantees

✅ **No Document Storage**
- If attacker breaches platform: no identity docs stolen
- Liability = $0 for document security

✅ **Compliance Audit Trail**
- Every verification traced to Stripe
- "We outsourced to Stripe" defense in regulatory review

✅ **User Consent**
- Terms explicitly state: "Documents verified by Stripe, not Platform"
- Privacy policy: "We don't collect/store documents"
- User cannot claim: "Platform lost my passport"

✅ **Regulatory Coverage**
- KYC: Stripe is responsible
- AML: Stripe screening handles it
- Sanctions: Stripe OFAC screening
- Platform: Only stores reference IDs

---

## Why This Works Legally

**Liability Framework:**
```
Traditional Escrow Model:
  ├─ Platform stores documents
  ├─ Platform = liable for breach
  └─ Platform = liable for "customer data compromise"

P2P + Stripe Connect Model:
  ├─ Platform = payment facilitator only
  ├─ Stripe = data controller (documents)
  ├─ Platform = data processor (reference IDs)
  └─ Breach liability = Stripe's, not Platform's
```

**Regulatory Argument:**
- "We are not a financial institution"
- "We are a software platform facilitating trades"
- "KYC/AML compliance delegated to payment provider"
- "Platform does not custody funds or documents"

This is the **correct legal architecture** for a marketplace that:
- Doesn't want to be a bank
- Doesn't want KYC/AML responsibility
- Wants to stay lean and compliant
- Avoids document security liability
