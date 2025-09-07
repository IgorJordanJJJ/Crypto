from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from .searchable_repository import SearchableRepository
from .filterable_repository import FilterableRepository
from ..schemas.crypto_schemas import CryptocurrencyFilter, PriceHistoryFilter


class CryptocurrencyRepository(SearchableRepository, FilterableRepository):
    """Репозиторий для работы с криптовалютами"""
    
    def __init__(self):
        super().__init__('cryptocurrencies')
    
    def search_cryptocurrencies(self, filter_params: CryptocurrencyFilter) -> List[Dict[str, Any]]:
        """Поиск криптовалют с фильтрацией"""
        if filter_params.search:
            return self.search(
                search_term=filter_params.search,
                search_fields=['name', 'symbol'],
                limit=filter_params.limit,
                offset=filter_params.offset
            )
        else:
            return self.find_all(
                limit=filter_params.limit,
                offset=filter_params.offset
            )
    
    def find_by_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Поиск криптовалюты по символу"""
        query = """
        SELECT * FROM cryptocurrencies
        WHERE symbol = %(symbol)s
        LIMIT 1
        """
        result = self.execute_query(query, {'symbol': symbol.lower()})
        
        if result.result_rows:
            return dict(zip(result.column_names, result.result_rows[0]))
        return None
    
    def find_top_by_market_cap(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Получение топ криптовалют по рыночной капитализации"""
        query = """
        SELECT * FROM cryptocurrencies
        WHERE market_cap_rank IS NOT NULL
        ORDER BY market_cap_rank ASC
        LIMIT %(limit)s
        """
        result = self.execute_query(query, {'limit': limit})
        return [dict(zip(result.column_names, row)) for row in result.result_rows]
    
    def get_cryptocurrencies_with_latest_price(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Получение криптовалют с последними ценами"""
        query = """
        SELECT 
            c.*,
            p.price_usd as current_price,
            p.price_change_24h,
            p.price_change_percentage_24h,
            p.market_cap,
            p.volume_24h,
            p.timestamp as price_timestamp
        FROM cryptocurrencies c
        LEFT JOIN (
            SELECT 
                cryptocurrency_id,
                price_usd,
                price_change_24h,
                price_change_percentage_24h,
                market_cap,
                volume_24h,
                timestamp,
                ROW_NUMBER() OVER (PARTITION BY cryptocurrency_id ORDER BY timestamp DESC) as rn
            FROM price_history
        ) p ON c.id = p.cryptocurrency_id AND p.rn = 1
        ORDER BY c.market_cap_rank ASC NULLS LAST
        LIMIT %(limit)s OFFSET %(offset)s
        """
        result = self.execute_query(query, {'limit': limit, 'offset': offset})
        return [dict(zip(result.column_names, row)) for row in result.result_rows]


