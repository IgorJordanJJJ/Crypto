from sqlalchemy import Column, String, DateTime, ForeignKey, DECIMAL, BigInteger
from sqlalchemy.orm import relationship
from .base import Base


class MarketData(Base):
    __tablename__ = "market_data"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    cryptocurrency_id = Column(String, ForeignKey("cryptocurrencies.id"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    total_supply = Column(DECIMAL(30, 2))
    circulating_supply = Column(DECIMAL(30, 2))
    max_supply = Column(DECIMAL(30, 2))
    ath = Column(DECIMAL(20, 8))  # All-time high
    atl = Column(DECIMAL(20, 8))  # All-time low
    ath_date = Column(DateTime)
    atl_date = Column(DateTime)
    roi_percentage = Column(DECIMAL(10, 4))
    # Additional market metrics
    spread_percentage = Column(DECIMAL(10, 6))  # (ask - bid) / ask * 100
    liquidity_score = Column(DECIMAL(10, 4))    # Based on bid/ask sizes
    
    # Relationship
    cryptocurrency = relationship("Cryptocurrency", back_populates="market_data")