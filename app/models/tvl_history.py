from sqlalchemy import Column, String, DateTime, ForeignKey, DECIMAL, BigInteger
from sqlalchemy.orm import relationship
from .base import Base


class TVLHistory(Base):
    __tablename__ = "tvl_history"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    protocol_id = Column(String, ForeignKey("defi_protocols.id"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    tvl = Column(DECIMAL(20, 2), nullable=False)
    tvl_change_24h = Column(DECIMAL(20, 2))
    tvl_change_percentage_24h = Column(DECIMAL(10, 4))
    
    # Relationship
    protocol = relationship("DeFiProtocol", back_populates="tvl_history")