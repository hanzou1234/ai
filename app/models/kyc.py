"""KYC (Know Your Customer) Models for user verification."""

from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, DateTime, Boolean, Enum as SQLEnum
from sqlalchemy.orm import declarative_base

from app.database import Base
from pydantic import BaseModel, ConfigDict
from typing import Optional

class KYCStatus(str, Enum):
    """KYC verification status states."""
    PENDING = "pending"           # 初期状態
    SUBMITTED = "submitted"       # 書類提出済み
    UNDER_REVIEW = "under_review" # 審査中
    VERIFIED = "verified"         # 承認済み
    REJECTED = "rejected"         # 却下
    EXPIRED = "expired"           # 期限切れ

class KYCStatusSchema(str, Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    VERIFIED = "verified"
    REJECTED = "rejected"
    EXPIRED = "expired"

class UserConsent(Base):
    """User's agreement to terms and privacy policy."""
    __tablename__ = "user_consent"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True)  # Agent ID
    
    # Consent tracking
    terms_accepted = Column(Boolean, default=False)
    privacy_accepted = Column(Boolean, default=False)
    aml_policy_accepted = Column(Boolean, default=False)
    
    # Timestamps
    terms_accepted_at = Column(DateTime, nullable=True)
    privacy_accepted_at = Column(DateTime, nullable=True)
    aml_policy_accepted_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def is_fully_compliant(self) -> bool:
        """Check if user has accepted all required policies."""
        return self.terms_accepted and self.privacy_accepted and self.aml_policy_accepted


class KYCRecord(Base):
    """
    KYC verification record for agents.
    
    ⚠️  IMPORTANT SECURITY NOTE:
    We DO NOT store identity documents on this platform.
    All KYC verification is delegated to Stripe Connect.
    
    This record only tracks:
    - Stripe verification status
    - User's Stripe Connected Account ID
    - Compliance flags
    
    Why? To eliminate platform liability for data breaches.
    If documents are compromised, Stripe (not us) bears the responsibility.
    """
    __tablename__ = "kyc_records"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True)  # Agent ID
    
    # Stripe Connection Details (Only what we store)
    stripe_connected_account_id = Column(String, unique=True, nullable=True, index=True)
    stripe_onboarding_link = Column(String, nullable=True)  # Temporary onboarding link
    
    # Verification Status (from Stripe, not us)
    status = Column(SQLEnum(KYCStatus), default=KYCStatus.PENDING, index=True)
    verification_date = Column(DateTime, nullable=True)
    
    # Compliance Flags (automated, no docs stored)
    sanctions_checked = Column(Boolean, default=False)  # Stripe handles
    aml_flagged = Column(Boolean, default=False)        # Stripe detects & flags
    
    # Metadata
    stripe_verification_status = Column(String, nullable=True)  # "verified", "pending", "rejected"
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def is_verified(self) -> bool:
        """Check if user is verified by Stripe."""
        return (
            self.status == KYCStatus.VERIFIED and 
            not self.aml_flagged and 
            self.stripe_connected_account_id is not None
        )

class KYCRecordSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    stripe_connected_account_id: Optional[str] = None
    stripe_verification_status: Optional[str] = None
    status: KYCStatusSchema
    sanctions_checked: bool = False
    aml_flagged: bool = False
    notes: Optional[str] = None
    verification_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
