from sqlalchemy import Column, String, Float, DateTime, Integer, ForeignKey, Text
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


class PriceHistory(Base):
    __tablename__ = "price_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    cryptocurrency_id = Column(String, ForeignKey("cryptocurrencies.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    price_usd = Column(Float, nullable=False)
    volume_24h = Column(Float)
    market_cap = Column(Float)
    price_change_24h = Column(Float)
    price_change_percentage_24h = Column(Float)
    
    # Relationship
    cryptocurrency = relationship("Cryptocurrency", back_populates="prices")


class MarketData(Base):
    __tablename__ = "market_data"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    cryptocurrency_id = Column(String, ForeignKey("cryptocurrencies.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    total_supply = Column(Float)
    circulating_supply = Column(Float)
    max_supply = Column(Float)
    ath = Column(Float)  # All-time high
    atl = Column(Float)  # All-time low
    ath_date = Column(DateTime)
    atl_date = Column(DateTime)
    roi_percentage = Column(Float)
    
    # Relationship
    cryptocurrency = relationship("Cryptocurrency", back_populates="market_data")


class DeFiProtocol(Base):
    __tablename__ = "defi_protocols"
    
    id = Column(String, primary_key=True)
    name = Column(String(100), nullable=False)
    category = Column(String(50))  # DEX, Lending, Yield Farming, etc.
    chain = Column(String(50))  # Ethereum, BSC, Polygon, etc.
    tvl = Column(Float)  # Total Value Locked
    native_token_id = Column(String, ForeignKey("cryptocurrencies.id"))
    website = Column(String(255))
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    native_token = relationship("Cryptocurrency", back_populates="defi_protocols")
    tvl_history = relationship("TVLHistory", back_populates="protocol", cascade="all, delete-orphan")


class TVLHistory(Base):
    __tablename__ = "tvl_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    protocol_id = Column(String, ForeignKey("defi_protocols.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    tvl = Column(Float, nullable=False)
    tvl_change_24h = Column(Float)
    tvl_change_percentage_24h = Column(Float)
    
    # Relationship
    protocol = relationship("DeFiProtocol", back_populates="tvl_history")