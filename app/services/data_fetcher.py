import asyncio
import httpx
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any, Optional
from ..core.config import settings


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


class BybitFetcher(DataFetcherBase):
    """
    Bybit API Fetcher - Free for public data, no API key required
    Documentation: https://bybit-exchange.github.io/docs/v5/intro
    """
    def __init__(self):
        super().__init__()
        self.base_url = settings.bybit_api_url
    
    async def fetch_tickers_info(self, category: str = "spot") -> List[Dict[str, Any]]:
        """Fetch all available symbols/tickers information"""
        url = f"{self.base_url}/market/instruments-info"
        params = {"category": category}  # spot, linear, option
        
        data = await self.retry_request(url, params)
        if data and data.get("result") and data.get("result").get("list"):
            return data["result"]["list"]
        return []
    
    async def fetch_ticker_24hr(self, category: str = "spot", symbol: str = None) -> List[Dict[str, Any]]:
        """Fetch 24hr ticker price change statistics"""
        url = f"{self.base_url}/market/tickers"
        params = {"category": category}
        
        if symbol:
            params["symbol"] = symbol
            
        data = await self.retry_request(url, params)
        if data and data.get("result") and data.get("result").get("list"):
            return data["result"]["list"]
        return []
    
    async def fetch_spot_symbols(self) -> List[Dict[str, Any]]:
        """Fetch all spot trading symbols with current prices"""
        # Get all USDT pairs (most liquid and popular)
        tickers = await self.fetch_ticker_24hr(category="spot")
        
        # Filter for USDT pairs and add basic crypto info
        spot_data = []
        for ticker in tickers:
            if ticker.get("symbol", "").endswith("USDT"):
                symbol_name = ticker.get("symbol", "").replace("USDT", "")
                spot_data.append({
                    "id": symbol_name.lower(),
                    "symbol": symbol_name,
                    "name": symbol_name,  # Bybit doesn't provide full names
                    "current_price": float(ticker.get("lastPrice", 0)),
                    "price_change_24h": float(ticker.get("price24hPcnt", 0)) * 100,  # Convert to percentage
                    "high_24h": float(ticker.get("highPrice24h", 0)),
                    "low_24h": float(ticker.get("lowPrice24h", 0)),
                    "volume_24h": float(ticker.get("volume24h", 0)),
                    "market_cap": None,  # Bybit doesn't provide market cap directly
                    "market_cap_rank": None
                })
        
        # Sort by volume (proxy for popularity)
        return sorted(spot_data, key=lambda x: x.get("volume_24h", 0), reverse=True)
    
    async def fetch_kline_history(self, symbol: str, interval: str = "1d", limit: int = 30) -> List[Dict[str, Any]]:
        """
        Fetch historical kline/candlestick data
        interval: 1m,3m,5m,15m,30m,1h,2h,4h,6h,12h,1d,1w,1M
        """
        url = f"{self.base_url}/market/kline"
        params = {
            "category": "spot",
            "symbol": f"{symbol.upper()}USDT",
            "interval": interval,
            "limit": limit
        }
        
        data = await self.retry_request(url, params)
        if data and data.get("result") and data.get("result").get("list"):
            klines = []
            for kline in data["result"]["list"]:
                # Bybit returns: [startTime, openPrice, highPrice, lowPrice, closePrice, volume, turnover]
                klines.append({
                    "timestamp": int(kline[0]),  # Unix timestamp in ms
                    "open": float(kline[1]),
                    "high": float(kline[2]), 
                    "low": float(kline[3]),
                    "close": float(kline[4]),
                    "volume": float(kline[5])
                })
            return sorted(klines, key=lambda x: x["timestamp"])  # Sort by time ascending
        return []
    
    async def fetch_data(self, **kwargs) -> List[Dict[str, Any]]:
        """Default method for fetching market data"""
        return await self.fetch_spot_symbols()


# Backward compatibility alias
CoinGeckoFetcher = BybitFetcher


class DefiLlamaFetcher(DataFetcherBase):
    """
    DefiLlama API Fetcher - Free, no API key required
    Documentation: https://defillama.com/docs/api
    """
    def __init__(self):
        super().__init__()
        self.base_url = settings.defillama_api_url
    
    async def fetch_protocols(self) -> List[Dict[str, Any]]:
        """Fetch all DeFi protocols with TVL data"""
        url = f"{self.base_url}/protocols"
        data = await self.retry_request(url)
        return data if data else []
    
    async def fetch_protocol_tvl_history(self, protocol_slug: str) -> Optional[Dict[str, Any]]:
        """Fetch TVL history for a specific protocol"""
        url = f"{self.base_url}/protocol/{protocol_slug}"
        return await self.retry_request(url)
    
    async def fetch_chains_tvl(self) -> List[Dict[str, Any]]:
        """Fetch TVL data for all blockchain networks"""
        url = f"{self.base_url}/chains"
        data = await self.retry_request(url)
        return data if data else []
    
    async def fetch_protocol_yields(self, protocol_id: str = None) -> List[Dict[str, Any]]:
        """Fetch yield farming data"""
        url = f"{self.base_url}/yields"
        params = {"protocol": protocol_id} if protocol_id else None
        data = await self.retry_request(url, params)
        return data.get("data", []) if data else []
    
    async def fetch_fees_revenue(self, protocol_id: str = None) -> Dict[str, Any]:
        """Fetch fees and revenue data"""
        if protocol_id:
            url = f"{self.base_url}/fees/{protocol_id}"
        else:
            url = f"{self.base_url}/overview/fees"
        data = await self.retry_request(url)
        return data if data else {}
    
    async def fetch_data(self, **kwargs) -> List[Dict[str, Any]]:
        return await self.fetch_protocols()


class YFinanceFetcher(DataFetcherBase):
    """
    Yahoo Finance Fetcher via yfinance - Free, no API key required
    Good for major cryptocurrencies with more detailed data
    """
    def __init__(self):
        super().__init__()
        # Popular crypto symbols supported by Yahoo Finance
        self.crypto_symbols = [
            "BTC-USD", "ETH-USD", "ADA-USD", "DOT-USD", "XRP-USD", 
            "LTC-USD", "BCH-USD", "LINK-USD", "BNB-USD", "SOL-USD",
            "MATIC-USD", "AVAX-USD", "UNI-USD", "ATOM-USD", "DOGE-USD",
            "SHIB-USD", "TRX-USD", "ETC-USD", "XLM-USD", "VET-USD"
        ]
    
    async def __aenter__(self):
        # yfinance doesn't need HTTP client
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
    
    async def fetch_crypto_data(self, symbols: List[str] = None) -> List[Dict[str, Any]]:
        """Fetch cryptocurrency data from Yahoo Finance"""
        import yfinance as yf
        import asyncio
        import pandas as pd
        from concurrent.futures import ThreadPoolExecutor
        
        symbols_to_fetch = symbols or self.crypto_symbols
        
        def fetch_single_crypto(symbol: str) -> Dict[str, Any]:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                hist = ticker.history(period="1d", interval="1d")
                
                if hist.empty:
                    return None
                
                # Get the latest data
                latest = hist.iloc[-1]
                
                # Extract symbol without -USD suffix
                clean_symbol = symbol.replace('-USD', '')
                
                return {
                    'id': clean_symbol.lower(),
                    'symbol': clean_symbol,
                    'name': info.get('longName', clean_symbol),
                    'current_price': float(latest['Close']) if not pd.isna(latest['Close']) else 0,
                    'market_cap': info.get('marketCap'),
                    'volume_24h': float(latest['Volume']) if not pd.isna(latest['Volume']) else 0,
                    'price_change_24h': float(latest['Close'] - latest['Open']) if not pd.isna(latest['Close']) and not pd.isna(latest['Open']) else 0,
                    'price_change_percentage_24h': ((float(latest['Close']) - float(latest['Open'])) / float(latest['Open']) * 100) if not pd.isna(latest['Close']) and not pd.isna(latest['Open']) and latest['Open'] != 0 else 0,
                    'high_24h': float(latest['High']) if not pd.isna(latest['High']) else 0,
                    'low_24h': float(latest['Low']) if not pd.isna(latest['Low']) else 0,
                    'circulating_supply': info.get('circulatingSupply'),
                    'total_supply': info.get('totalSupply'),
                    'max_supply': info.get('maxSupply'),
                    'market_cap_rank': None,  # YFinance doesn't provide rank
                    'ath': info.get('fiftyTwoWeekHigh'),
                    'atl': info.get('fiftyTwoWeekLow'),
                    'description': info.get('description', ''),
                    'website': info.get('website'),
                    'source': 'yfinance'
                }
            except Exception as e:
                print(f"Error fetching {symbol}: {e}")
                return None
        
        # Execute in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=5) as executor:
            tasks = [
                loop.run_in_executor(executor, fetch_single_crypto, symbol)
                for symbol in symbols_to_fetch
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out None results and exceptions
        valid_results = []
        for result in results:
            if result and not isinstance(result, Exception):
                valid_results.append(result)
        
        return valid_results
    
    async def fetch_crypto_history(self, symbol: str, period: str = "1mo", interval: str = "1d") -> List[Dict[str, Any]]:
        """Fetch historical data for a cryptocurrency"""
        import yfinance as yf
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        def fetch_history():
            try:
                ticker = yf.Ticker(f"{symbol.upper()}-USD")
                hist = ticker.history(period=period, interval=interval)
                
                history_data = []
                for timestamp, row in hist.iterrows():
                    history_data.append({
                        'timestamp': int(timestamp.timestamp() * 1000),  # Convert to milliseconds
                        'date': timestamp.strftime('%Y-%m-%d'),
                        'open': float(row['Open']),
                        'high': float(row['High']),
                        'low': float(row['Low']),
                        'close': float(row['Close']),
                        'volume': float(row['Volume']),
                        'symbol': symbol.upper()
                    })
                
                return history_data
            except Exception as e:
                print(f"Error fetching history for {symbol}: {e}")
                return []
        
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=1) as executor:
            result = await loop.run_in_executor(executor, fetch_history)
        
        return result
    
    async def fetch_data(self, **kwargs) -> List[Dict[str, Any]]:
        """Default method for fetching crypto data"""
        return await self.fetch_crypto_data()


# Backward compatibility alias
DeFiDataFetcher = DefiLlamaFetcher