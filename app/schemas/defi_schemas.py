from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from dataclasses import dataclass


class DeFiProtocolBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    category: Optional[str] = Field(None, max_length=50)
    chain: Optional[str] = Field(None, max_length=50)
    tvl: Optional[float] = Field(None, ge=0)
    native_token_id: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None


class DeFiProtocolCreate(DeFiProtocolBase):
    id: str = Field(..., min_length=1)


class DeFiProtocolUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    chain: Optional[str] = None
    tvl: Optional[float] = None
    native_token_id: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None


class DeFiProtocolResponse(DeFiProtocolBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TVLHistoryBase(BaseModel):
    timestamp: datetime
    tvl: float = Field(..., ge=0)
    tvl_change_24h: Optional[float] = None
    tvl_change_percentage_24h: Optional[float] = None


class TVLHistoryCreate(TVLHistoryBase):
    protocol_id: str


class TVLHistoryResponse(TVLHistoryBase):
    id: int
    protocol_id: str

    class Config:
        from_attributes = True


class DeFiProtocolDetailResponse(DeFiProtocolResponse):
    tvl_history: List[TVLHistoryResponse] = []


# Query filters
class DeFiProtocolFilter(BaseModel):
    category: Optional[str] = None
    chain: Optional[str] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class TVLHistoryFilter(BaseModel):
    protocol_id: str
    days: int = Field(default=30, ge=1, le=365)
    limit: int = Field(default=1000, ge=1, le=10000)


@dataclass
class DeFiProtocolListItem:
    """Dataclass для отображения в списке DeFi протоколов"""
    id: str
    name: str
    category: Optional[str]
    chain: Optional[str]
    tvl: Optional[float]
    tvl_change_24h: Optional[float]
    tvl_change_percentage_24h: Optional[float]
    updated_at: datetime


@dataclass
class TVLSummary:
    """Dataclass для суммарной статистики TVL"""
    total_tvl: float
    protocols_count: int
    top_protocol: Optional[str]
    top_protocol_tvl: Optional[float]