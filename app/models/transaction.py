from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from datetime import datetime
from app.database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String, primary_key=True, index=True)
    contract_id = Column(String, ForeignKey("contracts.id"))
    gross_amount = Column(Float)
    platform_fee = Column(Float)
    seller_net_payout = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    # type: ESCROW_DEPOSIT (old), PLATFORM_FEE (P2P model), PAYOUT (old)
    type = Column(String, default="PLATFORM_FEE")
