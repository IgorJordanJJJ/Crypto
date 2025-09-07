import asyncio
import httpx
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any, Optional
from ..core.config import settings
from ..core.database import clickhouse_manager


class DataFetcherBase(ABC):
    def __init__(self):
        self.client = None
        self.max_retries = settings.max_retries
        self.timeout = settings.request_timeout
    
    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()
    
    @abstractmethod
    async def fetch_data(self, **kwargs) -> List[Dict[str, Any]]:
        pass
    
    async def retry_request(self, url: str, params: Dict = None) -> Optional[Dict]:
        for attempt in range(self.max_retries):
            try:
                response = await self.client.get(url, params=params)
                response.raise_for_status()
                return response.json()
            except httpx.RequestError as e:
                if attempt == self.max_retries - 1:
                    raise e
                await asyncio.sleep(2 ** attempt)
        return None


class CoinGeckoFetcher(DataFetcherBase):
    def __init__(self):
        super().__init__()
        self.base_url = settings.coingecko_api_url
        self.api_key = settings.coingecko_api_key
    
    async def fetch_cryptocurrencies_list(self) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/coins/list"
        params = {"include_platform": "true"}
        
        if self.api_key:
            params["x_cg_demo_api_key"] = self.api_key
            
        data = await self.retry_request(url, params)
        return data if data else []
    
    async def fetch_cryptocurrency_details(self, coin_id: str) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}/coins/{coin_id}"
        params = {
            "localization": "false",
            "tickers": "false",
            "market_data": "true",
            "community_data": "false",
            "developer_data": "false",
            "sparkline": "false"
        }
        
        if self.api_key:
            params["x_cg_demo_api_key"] = self.api_key
            
        return await self.retry_request(url, params)
    
    async def fetch_market_data(self, vs_currency: str = "usd", per_page: int = 100, page: int = 1) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/coins/markets"
        params = {
            "vs_currency": vs_currency,
            "order": "market_cap_desc",
            "per_page": per_page,
            "page": page,
            "sparkline": "false",
            "price_change_percentage": "24h"
        }
        
        if self.api_key:
            params["x_cg_demo_api_key"] = self.api_key
            
        data = await self.retry_request(url, params)
        return data if data else []
    
    async def fetch_price_history(self, coin_id: str, vs_currency: str = "usd", days: int = 30) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}/coins/{coin_id}/market_chart"
        params = {
            "vs_currency": vs_currency,
            "days": days,
            "interval": "daily"
        }
        
        if self.api_key:
            params["x_cg_demo_api_key"] = self.api_key
            
        return await self.retry_request(url, params)
    
    async def fetch_data(self, **kwargs) -> List[Dict[str, Any]]:
        return await self.fetch_market_data()


class DeFiDataFetcher(DataFetcherBase):
    def __init__(self):
        super().__init__()
        self.defillama_base_url = "https://api.llama.fi"
    
    async def fetch_protocols(self) -> List[Dict[str, Any]]:
        url = f"{self.defillama_base_url}/protocols"
        data = await self.retry_request(url)
        return data if data else []
    
    async def fetch_protocol_tvl_history(self, protocol: str) -> Optional[Dict[str, Any]]:
        url = f"{self.defillama_base_url}/protocol/{protocol}"
        return await self.retry_request(url)
    
    async def fetch_chains_tvl(self) -> List[Dict[str, Any]]:
        url = f"{self.defillama_base_url}/chains"
        data = await self.retry_request(url)
        return data if data else []
    
    async def fetch_data(self, **kwargs) -> List[Dict[str, Any]]:
        return await self.fetch_protocols()