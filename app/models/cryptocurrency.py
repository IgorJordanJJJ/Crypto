from sqlalchemy import Column, String, Integer, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class Cryptocurrency(Base):
    __tablename__ = "cryptocurrencies"
    
    id = Column(String, primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    market_cap_rank = Column(Integer)
    description = Column(Text)
    website = Column(String(255))
    blockchain = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    prices = relationship("PriceHistory", back_populates="cryptocurrency", cascade="all, delete-orphan")
    market_data = relationship("MarketData", back_populates="cryptocurrency", cascade="all, delete-orphan")
    defi_protocols = relationship("DeFiProtocol", back_populates="native_token")