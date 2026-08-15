from sqlalchemy import Column, String, Float, Enum as SQLEnum, ForeignKey, JSON
import enum
from app.database import Base

class ContractStatus(enum.Enum):
    NEGOTIATING = "negotiating"
    PENDING_SUPERVISOR = "pending_supervisor"
    ESCROWED = "escrowed"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Contract(Base):
    __tablename__ = "contracts"

    id = Column(String, primary_key=True, index=True)
    buyer_id = Column(String, ForeignKey("agents.id"))
    seller_id = Column(String, ForeignKey("agents.id"))
    task_description = Column(String)
    agreed_price = Column(Float)
    status = Column(SQLEnum(ContractStatus), default=ContractStatus.NEGOTIATING)
    sla_details = Column(JSON)
    buyer_signature = Column(String, nullable=True)
    seller_signature = Column(String, nullable=True)
    buyer_supervisor_signature = Column(String, nullable=True)
    seller_supervisor_signature = Column(String, nullable=True)
    buyer_completion_signature = Column(String, nullable=True)
    seller_completion_signature = Column(String, nullable=True)
