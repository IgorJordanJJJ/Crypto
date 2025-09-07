from typing import List, Dict, Any
from datetime import datetime, timedelta
from .filterable_repository import FilterableRepository


class PriceHistoryRepository(FilterableRepository):
    """Репозиторий для работы с историей цен"""
    
    def __init__(self):
        super().__init__('price_history')
    
    def find_by_crypto_id(self, crypto_id: str, days: int = 30, limit: int = 1000) -> List[Dict[str, Any]]:
        """Получение истории цен для криптовалюты"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query = """
        SELECT * FROM price_history
        WHERE cryptocurrency_id = %(crypto_id)s
        AND timestamp >= %(start_date)s
        ORDER BY timestamp DESC
        LIMIT %(limit)s
        """
        
        result = self.execute_query(query, {
            'crypto_id': crypto_id,
            'start_date': start_date,
            'limit': limit
        })
        
        return [dict(zip(result.column_names, row)) for row in result.result_rows]
    
    def get_latest_prices(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Получение последних цен для всех криптовалют"""
        query = """
        SELECT 
            ph.*,
            c.name,
            c.symbol
        FROM price_history ph
        JOIN cryptocurrencies c ON ph.cryptocurrency_id = c.id
        WHERE ph.timestamp >= (now() - INTERVAL 1 DAY)
        ORDER BY ph.timestamp DESC
        LIMIT %(limit)s
        """
        
        result = self.execute_query(query, {'limit': limit})
        return [dict(zip(result.column_names, row)) for row in result.result_rows]
    
    def get_top_gainers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Получение топ растущих криптовалют за 24ч"""
        query = """
        SELECT 
            c.name,
            c.symbol,
            p.price_usd,
            p.price_change_percentage_24h
        FROM price_history p
        JOIN cryptocurrencies c ON p.cryptocurrency_id = c.id
        WHERE p.timestamp >= (now() - INTERVAL 1 DAY)
        AND p.price_change_percentage_24h > 0
        ORDER BY p.price_change_percentage_24h DESC
        LIMIT %(limit)s
        """
        
        result = self.execute_query(query, {'limit': limit})
        return [dict(zip(result.column_names, row)) for row in result.result_rows]
    
    def get_top_losers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Получение топ падающих криптовалют за 24ч"""
        query = """
        SELECT 
            c.name,
            c.symbol,
            p.price_usd,
            p.price_change_percentage_24h
        FROM price_history p
        JOIN cryptocurrencies c ON p.cryptocurrency_id = c.id
        WHERE p.timestamp >= (now() - INTERVAL 1 DAY)
        AND p.price_change_percentage_24h < 0
        ORDER BY p.price_change_percentage_24h ASC
        LIMIT %(limit)s
        """
        
        result = self.execute_query(query, {'limit': limit})
        return [dict(zip(result.column_names, row)) for row in result.result_rows]