from sqlalchemy import Column, String, DateTime, ForeignKey, DECIMAL, BigInteger
from sqlalchemy.orm import relationship
from .base import Base


class PriceHistory(Base):
    __tablename__ = "price_history"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    cryptocurrency_id = Column(String, ForeignKey("cryptocurrencies.id"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    price_usd = Column(DECIMAL(20, 8), nullable=False)
    volume_24h = Column(DECIMAL(20, 2))
    market_cap = Column(DECIMAL(20, 2))
    price_change_24h = Column(DECIMAL(20, 8))
    price_change_percentage_24h = Column(DECIMAL(10, 4))
    # Bybit specific fields
    bid_price = Column(DECIMAL(20, 8))  # Best bid price
    bid_size = Column(DECIMAL(20, 2))   # Volume at best bid
    ask_price = Column(DECIMAL(20, 8))  # Best ask price
    ask_size = Column(DECIMAL(20, 2))   # Volume at best ask
    prev_price_24h = Column(DECIMAL(20, 8))  # Price 24 hours ago
    turnover_24h = Column(DECIMAL(20, 2))    # 24h turnover in USD
    usd_index_price = Column(DECIMAL(20, 8)) # USD index price
    
    # Relationship
    cryptocurrency = relationship("Cryptocurrency", back_populates="prices")