import asyncio
from datetime import datetime
from typing import List, Dict, Any, Callable
from concurrent.futures import ThreadPoolExecutor
import logging
from ..core.config import settings
from ..core.database import clickhouse_manager
from .data_fetcher import CoinGeckoFetcher, DeFiDataFetcher


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
        self.coingecko_fetcher = CoinGeckoFetcher()
        self.defi_fetcher = DeFiDataFetcher()
    
    async def process_cryptocurrency_data(self) -> None:
        logger.info("Starting cryptocurrency data processing...")
        
        async with self.coingecko_fetcher as fetcher:
            # Fetch market data
            market_data = await fetcher.fetch_market_data(per_page=250)
            
            if not market_data:
                logger.error("Failed to fetch market data")
                return
            
            # Process cryptocurrencies
            cryptocurrencies = []
            price_history = []
            market_data_records = []
            
            for coin in market_data:
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
                    'volume_24h': coin.get('total_volume'),
                    'market_cap': coin.get('market_cap'),
                    'price_change_24h': coin.get('price_change_24h'),
                    'price_change_percentage_24h': coin.get('price_change_percentage_24h')
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
                    'ath_date': datetime.fromisoformat(coin['ath_date'].replace('Z', '+00:00')) if coin.get('ath_date') else None,
                    'atl_date': datetime.fromisoformat(coin['atl_date'].replace('Z', '+00:00')) if coin.get('atl_date') else None
                }
                market_data_records.append(market_record)
            
            # Insert data in batches
            await self.insert_data_batch('cryptocurrencies', cryptocurrencies)
            await self.insert_data_batch('price_history', price_history)
            await self.insert_data_batch('market_data', market_data_records)
            
            logger.info(f"Processed {len(cryptocurrencies)} cryptocurrencies")
    
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
                    'tvl': protocol.get('tvl', 0),
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow()
                }
                defi_protocols.append(protocol_record)
                
                # TVL history record
                tvl_record = {
                    'id': hash(f"{protocol_record['id']}_tvl_{datetime.utcnow().isoformat()}") % (2**63),
                    'protocol_id': protocol_record['id'],
                    'timestamp': datetime.utcnow(),
                    'tvl': protocol.get('tvl', 0),
                    'tvl_change_24h': protocol.get('change_1d', 0),
                    'tvl_change_percentage_24h': protocol.get('change_1d', 0)
                }
                tvl_history.append(tvl_record)
            
            # Insert data in batches
            await self.insert_data_batch('defi_protocols', defi_protocols)
            await self.insert_data_batch('tvl_history', tvl_history)
            
            logger.info(f"Processed {len(defi_protocols)} DeFi protocols")
    
    async def insert_data_batch(self, table: str, data: List[Dict[str, Any]]) -> None:
        if not data:
            return
        
        try:
            # Process data in batches to avoid memory issues
            await self.batch_processor.process_in_batches(
                data, 
                lambda batch: self._insert_batch_to_clickhouse(table, batch)
            )
        except Exception as e:
            logger.error(f"Error inserting data to {table}: {e}")
    
    async def _insert_batch_to_clickhouse(self, table: str, batch: List[Dict[str, Any]]) -> List[Any]:
        try:
            clickhouse_manager.insert_data(table, batch)
            return batch
        except Exception as e:
            logger.error(f"Error inserting batch to {table}: {e}")
            return []
    
    async def run_full_data_processing(self) -> None:
        logger.info("Starting full data processing pipeline...")
        
        # Initialize database and tables
        clickhouse_manager.create_database()
        clickhouse_manager.create_tables()
        
        # Process data concurrently
        tasks = [
            self.process_cryptocurrency_data(),
            self.process_defi_data()
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("Data processing pipeline completed!")


data_processor = DataProcessor()