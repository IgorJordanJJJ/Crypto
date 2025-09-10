from sqlalchemy import Column, String, DateTime, ForeignKey, DECIMAL, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class DeFiProtocol(Base):
    __tablename__ = "defi_protocols"
    
    id = Column(String, primary_key=True)
    name = Column(String(100), nullable=False, index=True)
    category = Column(String(50), index=True)  # DEX, Lending, Yield Farming, etc.
    chain = Column(String(50), index=True)  # Ethereum, BSC, Polygon, etc.
    tvl = Column(DECIMAL(20, 2))  # Total Value Locked
    native_token_id = Column(String, ForeignKey("cryptocurrencies.id"), index=True)
    website = Column(String(255))
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    native_token = relationship("Cryptocurrency", back_populates="defi_protocols")
    tvl_history = relationship("TVLHistory", back_populates="protocol", cascade="all, delete-orphan")