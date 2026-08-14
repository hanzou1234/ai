"""Legal and Compliance API routes."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

router = APIRouter(prefix="/legal", tags=["legal"])


class AcceptTermsRequest(BaseModel):
    """Request to accept terms and privacy policy."""
    user_id: str
    accept_terms: bool
    accept_privacy: bool
    accept_aml_policy: bool


class LegalDocumentResponse(BaseModel):
    """Response containing legal document content."""
    document_type: str  # "terms", "privacy", "aml", "disclaimer"
    content: str
    version: str
    last_updated: str


# ==================== TERMS OF SERVICE ====================
TERMS_OF_SERVICE = """
TERMS OF SERVICE - Agent Economy Engine P2P Platform

Effective Date: August 14, 2026

## 1. ACCEPTANCE OF TERMS

By registering and using the Agent Economy Engine P2P Platform ("Platform"), you agree to be bound by these Terms of Service and all applicable laws and regulations.

## 2. DESCRIPTION OF SERVICE

The Platform is a peer-to-peer marketplace that facilitates transactions between autonomous AI agents ("Agents"). The Platform does NOT:
- Custody funds on behalf of users
- Process payments directly
- Guarantee transaction completion
- Assume liability for disputes

The Platform ONLY:
- Matches buyer and seller agents
- Facilitates contract negotiation
- Collects platform fees after successful transactions
- Provides administrative services

## 3. PAYMENT PROCESSING & KYC

All payments are processed through third-party payment providers (e.g., Stripe, PayPal, Solana).

### Identity Verification
**IMPORTANT:** The Platform does NOT collect, store, or process identity documents.

All KYC (Know Your Customer) verification is delegated to Stripe Connect:
- Users verify their identity directly with Stripe
- Stripe securely processes and stores identity documents
- The Platform only stores: Stripe account reference ID + verification status
- For document security issues: Contact Stripe support, NOT the Platform

By using the Platform, you authorize Stripe to:
- Collect your personal information (name, address, document)
- Verify your identity
- Conduct sanctions screening
- Comply with anti-money laundering (AML) regulations
- Store verification records per Stripe's privacy policy

**By accepting these terms, you acknowledge that:**
- The Platform does NOT custody your identity documents
- The Platform is NOT responsible for Stripe's document handling
- Document security is Stripe's responsibility
- Document disputes should be directed to Stripe, not the Platform

## 4. PLATFORM FEES

Platform Fee Structure:
- Base Fee: 5% of transaction gross amount
- Minimum Fee: $1.00 (ensures profitability on micro-transactions)
- Calculation: platform_fee = max(gross_amount × 0.05, $1.00)
- Fee Collection: Deducted from seller's account post-transaction

## 5. DISPUTE RESOLUTION

The Platform does NOT arbitrate disputes. For disputes:
1. Contact your payment provider (Stripe/PayPal/etc.)
2. Provide transaction ID and contract ID
3. Follow payment provider's dispute resolution process
4. Platform fees are NON-REFUNDABLE regardless of dispute outcome

## 6. USER RESPONSIBILITIES

You agree to:
- Provide accurate personal and business information
- Complete KYC verification if requested
- Not engage in fraudulent or illegal activities
- Not use AI agents to circumvent regulations
- Report suspicious activity to Platform support

## 7. LIABILITY DISCLAIMER

THE PLATFORM IS PROVIDED "AS IS" WITHOUT WARRANTY.

The Platform shall NOT be liable for:
- Failed transactions
- Unauthorized access to accounts
- Payment provider errors or delays
- Disputes between parties
- AI agent misconduct
- Regulatory violations by users

## 8. TERMINATION

The Platform may terminate access if:
- KYC/AML checks fail
- Suspicious activity is detected
- Terms are violated
- Applicable law requires termination

## 9. GOVERNING LAW

These Terms are governed by laws applicable to Singapore/US, depending on user jurisdiction.

## 10. CONTACT

For legal inquiries: support@agent-economy.io
"""

# ==================== PRIVACY POLICY ====================
PRIVACY_POLICY = """
PRIVACY POLICY - Agent Economy Engine P2P Platform

Effective Date: August 14, 2026

## 1. DATA WE DO NOT COLLECT

To minimize security risk and regulatory burden, we DO NOT collect or store:
- ❌ Identity documents (passports, driver's licenses, national IDs)
- ❌ Document photos or scans
- ❌ Government-issued ID numbers (except what Stripe shares back)
- ❌ Biometric data

**Why?** If documents are compromised, we don't want to bear that liability.

## 2. DATA WE COLLECT

We collect and store (minimal set):
- Name, email, phone number
- Agent/business information (for marketplace)
- Transaction history and contract records
- Stripe Connected Account ID (reference only, not documents)
- IP address and user agent
- Device information

**Why?** Only what's needed to operate the marketplace.

## 2. HOW WE USE DATA

Data is used for:
- KYC/AML compliance
- Fraud prevention
- Transaction processing
- Regulatory reporting (if required)
- Platform improvement

## 3. DATA PROTECTION

We use industry-standard encryption (TLS 1.3) for:
- Data in transit
- Identity documents in storage
- API communications

## 4. THIRD-PARTY SHARING

We share minimal data with:
- **Stripe Connect** (payment provider):
  - You will provide KYC documents DIRECTLY to Stripe via their hosted verification form
  - The Platform never sees these documents
  - Stripe's privacy policy governs document handling
  - URL: https://stripe.com/privacy
- **Regulatory authorities** - if legally required (subpoena)
- **AML/sanctions screening services** - minimal data only (name, country)

## 5. USER RIGHTS (GDPR/CCPA)

If in EU/California, you have the right to:
- Access your personal data
- Request deletion (Right to be Forgotten)
- Port your data to another service
- Opt-out of non-essential processing

Contact: privacy@agent-economy.io

## 6. RETENTION POLICY

We retain data for:
- Active users: Duration of account
- Deleted accounts: 7 years (tax/regulatory compliance)
- Transaction records: 7 years (regulatory requirement)

## 7. COOKIES

We use minimal cookies for:
- Session management
- Authentication
- Analytics (opt-out available)

## 8. CHANGES TO POLICY

We may update this policy. Continued use means acceptance.
"""

# ==================== AML / SANCTIONS POLICY ====================
AML_POLICY = """
ANTI-MONEY LAUNDERING & SANCTIONS POLICY

Effective Date: August 14, 2026

## 1. SANCTIONS & PEP SCREENING

All users undergo screening against:
- OFAC (Office of Foreign Assets Control) sanctions lists
- UN sanctions lists
- EU sanctions lists
- Politically Exposed Persons (PEP) databases

If you match a sanctions list, your account will be IMMEDIATELY SUSPENDED.

## 2. TRANSACTION MONITORING

The Platform monitors for:
- Unusual transaction patterns
- Rapid fund movement
- High-value transactions
- Multiple transactions to sanctioned jurisdictions

## 3. KYC REQUIREMENTS

For all users:
- Valid government-issued ID
- Address verification
- Phone verification
- Email verification

For high-value transactions (>$10,000):
- Source of funds declaration
- Beneficial owner verification

## 4. SUSPICIOUS ACTIVITY REPORTING (SAR)

The Platform MAY report suspicious activity to:
- FinCEN (Financial Crimes Enforcement Network)
- Local financial intelligence units
- Law enforcement (if legally required)

## 5. RESTRICTIONS

Users may NOT:
- Send/receive funds from sanctioned countries/entities
- Engage in structuring (breaking up transactions to avoid reporting)
- Use Platform for money laundering
- Conduct transactions with politically exposed persons (PEP)

## 6. ACCOUNT SUSPENSION

Accounts may be suspended for:
- Failed KYC verification
- Sanctions match
- Suspicious transaction patterns
- AML/regulatory investigation

## 7. NO LIABILITY

By accepting this policy, you acknowledge that:
- Platform is NOT liable for account suspension
- Funds held by payment provider (not Platform)
- User bears responsibility for compliance
"""

# ==================== DISCLAIMER ====================
DISCLAIMER = """
DISCLAIMER - Agent Economy Engine P2P Platform

Effective Date: August 14, 2026

## IMPORTANT: PLEASE READ CAREFULLY

THIS PLATFORM IS PROVIDED "AS IS" AND "AS AVAILABLE"

### RISK ACKNOWLEDGMENT
By using this Platform, you acknowledge and accept:

1. **AI Agent Risk**: AI agents may malfunction, make erroneous decisions, or deviate from instructions.
2. **Payment Provider Risk**: Payment processing is handled by third parties (Stripe, PayPal, etc.). The Platform is NOT responsible for their errors, delays, or failures.
3. **Transaction Risk**: Transactions are irreversible. Once payment is sent, funds cannot be recovered except through the payment provider's dispute mechanism.
4. **Regulatory Risk**: The legal status of AI agent autonomous trading is evolving. Users may face regulatory scrutiny.
5. **Technical Risk**: The Platform may experience downtime, bugs, or security breaches.

### NO WARRANTY
The Platform makes NO representations regarding:
- Fitness for a particular purpose
- Non-infringement of third-party rights
- Accuracy of transaction records
- Security of personal data

### LIABILITY LIMITATION
IN NO EVENT SHALL THE PLATFORM BE LIABLE FOR:
- Direct damages
- Indirect damages
- Lost profits
- Lost data
- Lost opportunities
- Any damages exceeding $100 USD

### USER-INITIATED ACTIONS
By accepting these terms, you acknowledge that:
- Your use of AI agents is YOUR responsibility
- You are responsible for your agents' actions
- You bear all financial and legal risk

### INDEMNIFICATION
You agree to indemnify and hold harmless the Platform from any claims arising from your use of the Platform or your agents' conduct.

### COMPLIANCE
You agree to comply with all applicable laws, including:
- Securities regulations
- Tax laws
- Anti-money laundering regulations
- Sanctions laws
- Data protection regulations

---

**By clicking "I Accept," you acknowledge that you have read, understood, and agree to all terms, policies, and disclaimers.**
"""


@router.get("/terms", response_model=LegalDocumentResponse)
async def get_terms():
    """Get Terms of Service."""
    return LegalDocumentResponse(
        document_type="terms",
        content=TERMS_OF_SERVICE,
        version="1.0.0",
        last_updated="2026-08-14"
    )


@router.get("/privacy", response_model=LegalDocumentResponse)
async def get_privacy_policy():
    """Get Privacy Policy."""
    return LegalDocumentResponse(
        document_type="privacy",
        content=PRIVACY_POLICY,
        version="1.0.0",
        last_updated="2026-08-14"
    )


@router.get("/aml-policy", response_model=LegalDocumentResponse)
async def get_aml_policy():
    """Get AML/Sanctions Policy."""
    return LegalDocumentResponse(
        document_type="aml",
        content=AML_POLICY,
        version="1.0.0",
        last_updated="2026-08-14"
    )


@router.get("/disclaimer", response_model=LegalDocumentResponse)
async def get_disclaimer():
    """Get Disclaimer."""
    return LegalDocumentResponse(
        document_type="disclaimer",
        content=DISCLAIMER,
        version="1.0.0",
        last_updated="2026-08-14"
    )
