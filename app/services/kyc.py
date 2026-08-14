"""KYC Service for user verification - Stripe Connect Delegated."""

from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.kyc import KYCRecord, KYCStatus, UserConsent
from app.models.agent import Agent
from app.config import settings


class KYCService:
    """
    Service for managing KYC verification via Stripe Connect.
    
    SECURITY DESIGN:
    - We DO NOT store identity documents
    - All KYC is delegated to Stripe Connect
    - Platform only stores: Stripe Connected Account ID + verification status
    - Liability: Stripe bears responsibility for document security
    """
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def create_kyc_record_for_agent(self, user_id: str) -> KYCRecord:
        """
        Create a KYC record and prepare for Stripe Connect onboarding.
        
        User must be redirected to Stripe's hosted onboarding form.
        We do NOT ask for documents directly.
        """
        kyc_record = KYCRecord(
            id=f"kyc_{user_id}_{datetime.utcnow().timestamp()}",
            user_id=user_id,
            status=KYCStatus.PENDING,
            sanctions_checked=False,
            aml_flagged=False
        )
        self.db.add(kyc_record)
        await self.db.commit()
        await self.db.refresh(kyc_record)
        return kyc_record
    
    async def get_kyc_record(self, user_id: str) -> Optional[KYCRecord]:
        """Retrieve KYC record by user ID."""
        result = await self.db.execute(
            select(KYCRecord).where(KYCRecord.user_id == user_id)
        )
        return result.scalars().first()
    
    async def update_stripe_account(
        self,
        user_id: str,
        stripe_connected_account_id: str,
        onboarding_link: str = None
    ) -> KYCRecord:
        """
        Update with Stripe Connected Account ID after user completes onboarding.
        
        ⚠️  This is called AFTER user returns from Stripe's hosted form.
        The user's identity documents are now stored with Stripe, not us.
        """
        kyc_record = await self.get_kyc_record(user_id)
        if not kyc_record:
            raise ValueError(f"KYC record not found for user {user_id}")
        
        kyc_record.stripe_connected_account_id = stripe_connected_account_id
        if onboarding_link:
            kyc_record.stripe_onboarding_link = onboarding_link
        kyc_record.status = KYCStatus.SUBMITTED
        kyc_record.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(kyc_record)
        return kyc_record
    
    async def verify_from_stripe(
        self,
        user_id: str,
        stripe_status: str,  # "verified", "pending", "rejected"
        notes: str = None
    ) -> KYCRecord:
        """
        Update verification status based on Stripe's verification result.
        
        Called when we receive webhook from Stripe:
        account.updated event with verification status.
        """
        kyc_record = await self.get_kyc_record(user_id)
        if not kyc_record:
            raise ValueError(f"KYC record not found for user {user_id}")
        
        # Map Stripe status to our KYCStatus
        if stripe_status == "verified":
            kyc_record.status = KYCStatus.VERIFIED
            kyc_record.verification_date = datetime.utcnow()
        elif stripe_status == "rejected":
            kyc_record.status = KYCStatus.REJECTED
        else:  # pending, under_review
            kyc_record.status = KYCStatus.UNDER_REVIEW
        
        kyc_record.stripe_verification_status = stripe_status
        if notes:
            kyc_record.notes = notes
        kyc_record.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(kyc_record)
        return kyc_record
    
    async def flag_aml(self, user_id: str, reason: str) -> KYCRecord:
        """
        Flag user for AML (Anti-Money Laundering) based on Stripe's screening.
        
        When Stripe detects sanctions match or suspicious activity.
        """
        kyc_record = await self.get_kyc_record(user_id)
        if not kyc_record:
            raise ValueError(f"KYC record not found for user {user_id}")
        
        kyc_record.aml_flagged = True
        kyc_record.status = KYCStatus.UNDER_REVIEW
        kyc_record.notes = f"AML Flag (Stripe): {reason}"
        kyc_record.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(kyc_record)
        return kyc_record
    
    async def is_verified(self, user_id: str) -> bool:
        """Check if user is KYC verified and not flagged."""
        kyc_record = await self.get_kyc_record(user_id)
        if not kyc_record:
            return False
        return kyc_record.is_verified()


class ConsentService:
    """Service for managing user consent to legal documents."""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def get_or_create_consent(self, user_id: str) -> UserConsent:
        """Get or create user consent record."""
        result = await self.db.execute(
            select(UserConsent).where(UserConsent.user_id == user_id)
        )
        consent = result.scalars().first()
        
        if not consent:
            consent = UserConsent(
                id=f"consent_{user_id}_{datetime.utcnow().timestamp()}",
                user_id=user_id
            )
            self.db.add(consent)
            await self.db.commit()
            await self.db.refresh(consent)
        
        return consent
    
    async def accept_terms(self, user_id: str) -> UserConsent:
        """Mark terms as accepted."""
        consent = await self.get_or_create_consent(user_id)
        consent.terms_accepted = True
        consent.terms_accepted_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(consent)
        return consent
    
    async def accept_privacy(self, user_id: str) -> UserConsent:
        """Mark privacy policy as accepted."""
        consent = await self.get_or_create_consent(user_id)
        consent.privacy_accepted = True
        consent.privacy_accepted_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(consent)
        return consent
    
    async def accept_aml_policy(self, user_id: str) -> UserConsent:
        """Mark AML policy as accepted."""
        consent = await self.get_or_create_consent(user_id)
        consent.aml_policy_accepted = True
        consent.aml_policy_accepted_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(consent)
        return consent
    
    async def accept_all(self, user_id: str) -> UserConsent:
        """Mark all policies as accepted."""
        consent = await self.get_or_create_consent(user_id)
        consent.terms_accepted = True
        consent.privacy_accepted = True
        consent.aml_policy_accepted = True
        
        now = datetime.utcnow()
        consent.terms_accepted_at = now
        consent.privacy_accepted_at = now
        consent.aml_policy_accepted_at = now
        
        await self.db.commit()
        await self.db.refresh(consent)
        return consent
    
    async def is_fully_compliant(self, user_id: str) -> bool:
        """Check if user has accepted all required policies."""
        consent = await self.get_or_create_consent(user_id)
        return consent.is_fully_compliant()
