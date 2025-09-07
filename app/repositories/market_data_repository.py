from typing import List, Dict, Any
from datetime import datetime, timedelta
from .filterable_repository import FilterableRepository


class MarketDataRepository(FilterableRepository):
    """Репозиторий для работы с рыночными данными"""
    
    def __init__(self):
        super().__init__('market_data')
    
    def find_by_crypto_id(self, crypto_id: str, days: int = 30, limit: int = 1000) -> List[Dict[str, Any]]:
        """Получение рыночных данных для криптовалюты"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query = """
        SELECT * FROM market_data
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
    
    def get_market_summary(self) -> Dict[str, Any]:
        """Получение сводной рыночной статистики"""
        query = """
        SELECT 
            count(DISTINCT cryptocurrency_id) as total_assets,
            sum(circulating_supply * (
                SELECT price_usd 
                FROM price_history ph 
                WHERE ph.cryptocurrency_id = md.cryptocurrency_id 
                ORDER BY timestamp DESC 
                LIMIT 1
            )) as total_market_cap,
            avg(roi_percentage) as avg_roi
        FROM market_data md
        WHERE timestamp >= (now() - INTERVAL 1 DAY)
        """
        
        result = self.execute_query(query)
        if result.result_rows:
            return dict(zip(result.column_names, result.result_rows[0]))
        return {}