import asyncio
from datetime import datetime
from typing import List, Dict, Any, Callable
from concurrent.futures import ThreadPoolExecutor
import logging
from ..core.config import settings
from ..core.database import get_db
from ..repositories.crypto_repository import CryptocurrencyRepository
from ..repositories.defi_repository import DeFiProtocolRepository
from .data_fetcher import BybitFetcher, DefiLlamaFetcher, YFinanceFetcher


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BatchProcessor:
    def __init__(self):
        self.batch_size = settings.batch_size
        self.max_workers = 5
    
    async def process_in_batches(
        self, 
        data: List[Any], 
        processor_func: Callable,
        batch_size: int = None
    ) -> List[Any]:
        batch_size = batch_size or self.batch_size
        results = []
        
        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            batch_results = await processor_func(batch)
            results.extend(batch_results)
            
            # Small delay to prevent rate limiting
            await asyncio.sleep(0.1)
        
        return results
    
    async def concurrent_process(
        self, 
        items: List[Any], 
        processor_func: Callable,
        max_workers: int = None
    ) -> List[Any]:
        max_workers = max_workers or self.max_workers
        semaphore = asyncio.Semaphore(max_workers)
        
        async def process_with_semaphore(item):
            async with semaphore:
                return await processor_func(item)
        
        tasks = [process_with_semaphore(item) for item in items]
        return await asyncio.gather(*tasks, return_exceptions=True)


class DataProcessor:
    def __init__(self):
        self.batch_processor = BatchProcessor()
        self.bybit_fetcher = BybitFetcher()
        self.yfinance_fetcher = YFinanceFetcher()
        self.defi_fetcher = DefiLlamaFetcher()
    
    async def process_cryptocurrency_data(self) -> None:
        logger.info("Starting cryptocurrency data processing...")
        
        # Fetch data from both sources
        bybit_data = []
        yfinance_data = []
        
        # Fetch from Bybit
        async with self.bybit_fetcher as fetcher:
            bybit_data = await fetcher.fetch_spot_symbols()
            if bybit_data:
                logger.info(f"Fetched {len(bybit_data)} cryptocurrencies from Bybit")
        
        # Fetch from YFinance
        async with self.yfinance_fetcher as fetcher:
            yfinance_data = await fetcher.fetch_crypto_data()
            if yfinance_data:
                logger.info(f"Fetched {len(yfinance_data)} cryptocurrencies from YFinance")
        
        # Combine and deduplicate data (prefer YFinance data when available)
        market_data = self._merge_crypto_data(bybit_data, yfinance_data)
        
        if not market_data:
            logger.error("Failed to fetch market data from any source")
            return
        
        logger.info(f"Starting data processing for {len(market_data)} merged cryptocurrencies")
        
        # Process cryptocurrencies
        cryptocurrencies = []
        price_history = []
        market_data_records = []
        
        try:
            for coin in market_data:
                logger.debug(f"Processing coin: {coin.get('id', 'unknown')}")
                # Cryptocurrency record
                crypto_record = {
                    'id': coin['id'],
                    'symbol': coin['symbol'],
                    'name': coin['name'],
                    'market_cap_rank': coin.get('market_cap_rank'),
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow()
                }
                cryptocurrencies.append(crypto_record)
                
                # Price history record
                price_record = {
                    'id': hash(f"{coin['id']}_{datetime.utcnow().isoformat()}") % (2**63),
                    'cryptocurrency_id': coin['id'],
                    'timestamp': datetime.utcnow(),
                    'price_usd': coin.get('current_price', 0),
                    'volume_24h': coin.get('volume_24h'),  # Bybit field
                    'market_cap': coin.get('market_cap'),  # None from Bybit
                    'price_change_24h': coin.get('price_change_24h'),  # Bybit % converted to absolute
                    'price_change_percentage_24h': coin.get('price_change_24h'),  # Bybit % field
                    # Bybit specific fields
                    'bid_price': coin.get('bid_price'),
                    'bid_size': coin.get('bid_size'),
                    'ask_price': coin.get('ask_price'),
                    'ask_size': coin.get('ask_size'),
                    'prev_price_24h': coin.get('prev_price_24h'),
                    'turnover_24h': coin.get('turnover_24h'),
                    'usd_index_price': coin.get('usd_index_price')
                }
                price_history.append(price_record)
                
                # Market data record
                market_record = {
                    'id': hash(f"{coin['id']}_market_{datetime.utcnow().isoformat()}") % (2**63),
                    'cryptocurrency_id': coin['id'],
                    'timestamp': datetime.utcnow(),
                    'total_supply': coin.get('total_supply'),
                    'circulating_supply': coin.get('circulating_supply'),
                    'max_supply': coin.get('max_supply'),
                    'ath': coin.get('ath'),
                    'atl': coin.get('atl'),
                    'ath_date': None,  # YFinance/Bybit don't provide formatted dates
                    'atl_date': None,  # YFinance/Bybit don't provide formatted dates
                    # Additional market metrics
                    'spread_percentage': coin.get('spread_percentage'),
                    'liquidity_score': coin.get('liquidity_score')
                }
                market_data_records.append(market_record)
            
            # Insert data in batches
            logger.info(f"About to insert {len(cryptocurrencies)} cryptocurrencies")
            await self.insert_data_batch('cryptocurrencies', cryptocurrencies)
            
            logger.info(f"About to insert {len(price_history)} price_history records")
            await self.insert_data_batch('price_history', price_history)
            
            logger.info(f"About to insert {len(market_data_records)} market_data records")
            await self.insert_data_batch('market_data', market_data_records)
            
            logger.info(f"Processed {len(cryptocurrencies)} cryptocurrencies")
            
        except Exception as e:
            logger.error(f"Error processing cryptocurrency data: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise
    
    async def process_defi_data(self) -> None:
        logger.info("Starting DeFi data processing...")
        
        async with self.defi_fetcher as fetcher:
            # Fetch protocols data
            protocols = await fetcher.fetch_protocols()
            
            if not protocols:
                logger.error("Failed to fetch DeFi protocols data")
                return
            
            defi_protocols = []
            tvl_history = []
            
            for protocol in protocols[:100]:  # Limit to top 100 for initial load
                # DeFi protocol record
                protocol_record = {
                    'id': protocol.get('id', protocol['name'].lower().replace(' ', '-')),
                    'name': protocol['name'],
                    'category': protocol.get('category', 'Unknown'),
                    'chain': protocol.get('chain', 'Unknown'),
                    'tvl': protocol.get('tvl') or 0,
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow()
                }
                defi_protocols.append(protocol_record)
                
                # TVL history record
                tvl_record = {
                    'id': hash(f"{protocol_record['id']}_tvl_{datetime.utcnow().isoformat()}") % (2**63),
                    'protocol_id': protocol_record['id'],
                    'timestamp': datetime.utcnow(),
                    'tvl': protocol.get('tvl') or 0,
                    'tvl_change_24h': protocol.get('change_1d', 0),
                    'tvl_change_percentage_24h': protocol.get('change_1d', 0)
                }
                tvl_history.append(tvl_record)
            
            # Insert data in batches
            await self.insert_data_batch('defi_protocols', defi_protocols)
            await self.insert_data_batch('tvl_history', tvl_history)
            
            logger.info(f"Processed {len(defi_protocols)} DeFi protocols")
    
    async def insert_data_batch(self, table: str, data: List[Dict[str, Any]]) -> None:
        logger.info(f"insert_data_batch called with table={table}, data_length={len(data) if data else 0}")
        if not data:
            logger.info(f"No data to insert for table {table}")
            return
        
        try:
            # Process data in batches to avoid memory issues
            async def insert_wrapper(batch):
                return await self._insert_batch_to_database(table, batch)
            
            await self.batch_processor.process_in_batches(
                data, 
                insert_wrapper
            )
        except Exception as e:
            logger.error(f"Error inserting data to {table}: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
    
    async def _insert_batch_to_database(self, table: str, batch: List[Dict[str, Any]]) -> List[Any]:
        """Insert batch data to PostgreSQL database using repositories"""
        logger.info(f"_insert_batch_to_database called with table={table}, batch_size={len(batch)}")
        try:
            from ..repositories.crypto_repository import CryptocurrencyRepository
            from ..repositories.price_history_repository import PriceHistoryRepository
            from ..repositories.market_data_repository import MarketDataRepository
            from ..repositories.defi_repository import DeFiProtocolRepository
            from ..repositories.tvl_history_repository import TVLHistoryRepository
            from ..models import Cryptocurrency, PriceHistory, MarketData, DeFiProtocol, TVLHistory
            
            if table == 'cryptocurrencies':
                repo = CryptocurrencyRepository()
                for record in batch:
                    crypto = Cryptocurrency(**record)
                    existing = repo.find_by_id(record['id'])
                    if existing:
                        repo.update(existing.id, record)
                    else:
                        repo.create(crypto)
                        
            elif table == 'price_history':
                repo = PriceHistoryRepository()
                for record in batch:
                    price = PriceHistory(**record)
                    repo.create(price)
                    
            elif table == 'market_data':
                repo = MarketDataRepository()
                for record in batch:
                    market = MarketData(**record)
                    repo.create(market)
                    
            elif table == 'defi_protocols':
                repo = DeFiProtocolRepository()
                for record in batch:
                    protocol = DeFiProtocol(**record)
                    existing = repo.find_by_id(record['id'])
                    if existing:
                        repo.update(existing.id, record)
                    else:
                        repo.create(protocol)
                        
            elif table == 'tvl_history':
                repo = TVLHistoryRepository()
                for record in batch:
                    tvl = TVLHistory(**record)
                    repo.create(tvl)
            
            logger.info(f"Successfully inserted {len(batch)} records to {table}")
            return batch
        except Exception as e:
            logger.error(f"Error inserting batch to {table}: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return []
    
    async def run_full_data_processing(self) -> None:
        logger.info("Starting full data processing pipeline...")
        
        # Database is initialized via Alembic migrations
        logger.info("Database should be initialized via migrations")
        
        # Process data concurrently
        tasks = [
            self.process_cryptocurrency_data(),
            self.process_defi_data()
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("Data processing pipeline completed!")
    
    def _merge_crypto_data(self, bybit_data: List[Dict[str, Any]], yfinance_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Объединение данных из Bybit и YFinance, приоритет у YFinance"""
        merged = {}
        
        # Добавляем данные из Bybit
        for coin in bybit_data:
            coin_id = coin.get('id')
            if coin_id:
                merged[coin_id] = {**coin, 'source': 'bybit'}
        
        # Обновляем/добавляем данные из YFinance (приоритет)
        for coin in yfinance_data:
            coin_id = coin.get('id')
            if coin_id:
                if coin_id in merged:
                    # Объединяем данные, YFinance имеет приоритет
                    merged_coin = merged[coin_id].copy()
                    merged_coin.update(coin)
                    merged_coin['source'] = 'yfinance+bybit'
                    merged[coin_id] = merged_coin
                else:
                    merged[coin_id] = {**coin, 'source': 'yfinance'}
        
        logger.info(f"Merged data: {len(merged)} unique cryptocurrencies")
        return list(merged.values())


data_processor = DataProcessor()