from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from dataclasses import dataclass


class CryptocurrencyBase(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=100)
    market_cap_rank: Optional[int] = None
    description: Optional[str] = None
    website: Optional[str] = None
    blockchain: Optional[str] = None


class CryptocurrencyCreate(CryptocurrencyBase):
    id: str = Field(..., min_length=1)


class CryptocurrencyUpdate(BaseModel):
    symbol: Optional[str] = None
    name: Optional[str] = None
    market_cap_rank: Optional[int] = None
    description: Optional[str] = None
    website: Optional[str] = None
    blockchain: Optional[str] = None


class CryptocurrencyResponse(CryptocurrencyBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PriceHistoryBase(BaseModel):
    timestamp: datetime
    price_usd: float = Field(..., ge=0)
    volume_24h: Optional[float] = Field(None, ge=0)
    market_cap: Optional[float] = Field(None, ge=0)
    price_change_24h: Optional[float] = None
    price_change_percentage_24h: Optional[float] = None


class PriceHistoryCreate(PriceHistoryBase):
    cryptocurrency_id: str


class PriceHistoryResponse(PriceHistoryBase):
    id: int
    cryptocurrency_id: str

    class Config:
        from_attributes = True


class MarketDataBase(BaseModel):
    timestamp: datetime
    total_supply: Optional[float] = Field(None, ge=0)
    circulating_supply: Optional[float] = Field(None, ge=0)
    max_supply: Optional[float] = Field(None, ge=0)
    ath: Optional[float] = Field(None, ge=0)
    atl: Optional[float] = Field(None, ge=0)
    ath_date: Optional[datetime] = None
    atl_date: Optional[datetime] = None
    roi_percentage: Optional[float] = None


class MarketDataCreate(MarketDataBase):
    cryptocurrency_id: str


class MarketDataResponse(MarketDataBase):
    id: int
    cryptocurrency_id: str

    class Config:
        from_attributes = True


class CryptocurrencyDetailResponse(CryptocurrencyResponse):
    price_history: List[PriceHistoryResponse] = []
    market_data: List[MarketDataResponse] = []


# Query filters
class CryptocurrencyFilter(BaseModel):
    search: Optional[str] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class PriceHistoryFilter(BaseModel):
    cryptocurrency_id: str
    days: int = Field(default=30, ge=1, le=365)
    limit: int = Field(default=1000, ge=1, le=10000)


@dataclass
class CryptocurrencyListItem:
    """Dataclass для отображения в списке криптовалют"""
    id: str
    symbol: str
    name: str
    market_cap_rank: Optional[int]
    current_price: Optional[float]
    price_change_24h: Optional[float]
    price_change_percentage_24h: Optional[float]
    market_cap: Optional[float]
    updated_at: datetime