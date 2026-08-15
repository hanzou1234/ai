from sqlalchemy import Column, String, Float, JSON
from app.database import Base

class Agent(Base):
    __tablename__ = "agents"

    id = Column(String, primary_key=True, index=True) # UUID or Identifier
    name = Column(String, unique=True, index=True)
    capabilities = Column(JSON) # MCP compliant
    base_price = Column(Float, default=10.0)
    wallet_balance = Column(Float, default=0.0)
    rating = Column(Float, default=5.0)
    signing_public_key = Column(String, nullable=True)
    supervisor_public_key = Column(String, nullable=True)
