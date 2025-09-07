from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from .searchable_repository import SearchableRepository
from .filterable_repository import FilterableRepository
from ..schemas.defi_schemas import DeFiProtocolFilter, TVLHistoryFilter


class DeFiProtocolRepository(SearchableRepository, FilterableRepository):
    """Репозиторий для работы с DeFi протоколами"""
    
    def __init__(self):
        super().__init__('defi_protocols')
    
    def search_protocols(self, filter_params: DeFiProtocolFilter) -> List[Dict[str, Any]]:
        """Поиск DeFi протоколов с фильтрацией"""
        filters = {}
        
        if filter_params.category:
            filters['category'] = filter_params.category
        
        if filter_params.chain:
            filters['chain'] = filter_params.chain
        
        return self.find_with_filters(
            filters=filters,
            limit=filter_params.limit,
            offset=filter_params.offset,
            order_by='tvl',
            order_direction='DESC'
        )
    
    def find_by_category(self, category: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Поиск протоколов по категории"""
        query = """
        SELECT * FROM defi_protocols
        WHERE category = %(category)s
        ORDER BY tvl DESC NULLS LAST
        LIMIT %(limit)s
        """
        result = self.execute_query(query, {'category': category, 'limit': limit})
        return [dict(zip(result.column_names, row)) for row in result.result_rows]
    
    def find_by_chain(self, chain: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Поиск протоколов по блокчейну"""
        query = """
        SELECT * FROM defi_protocols
        WHERE chain = %(chain)s
        ORDER BY tvl DESC NULLS LAST
        LIMIT %(limit)s
        """
        result = self.execute_query(query, {'chain': chain, 'limit': limit})
        return [dict(zip(result.column_names, row)) for row in result.result_rows]
    
    def get_top_by_tvl(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Получение топ протоколов по TVL"""
        query = """
        SELECT * FROM defi_protocols
        WHERE tvl > 0
        ORDER BY tvl DESC
        LIMIT %(limit)s
        """
        result = self.execute_query(query, {'limit': limit})
        return [dict(zip(result.column_names, row)) for row in result.result_rows]
    
    def get_protocols_with_latest_tvl(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Получение протоколов с последними данными TVL"""
        query = """
        SELECT 
            dp.*,
            tvl_h.tvl as current_tvl,
            tvl_h.tvl_change_24h,
            tvl_h.tvl_change_percentage_24h,
            tvl_h.timestamp as tvl_timestamp
        FROM defi_protocols dp
        LEFT JOIN (
            SELECT 
                protocol_id,
                tvl,
                tvl_change_24h,
                tvl_change_percentage_24h,
                timestamp,
                ROW_NUMBER() OVER (PARTITION BY protocol_id ORDER BY timestamp DESC) as rn
            FROM tvl_history
        ) tvl_h ON dp.id = tvl_h.protocol_id AND tvl_h.rn = 1
        ORDER BY COALESCE(tvl_h.tvl, dp.tvl, 0) DESC
        LIMIT %(limit)s OFFSET %(offset)s
        """
        result = self.execute_query(query, {'limit': limit, 'offset': offset})
        return [dict(zip(result.column_names, row)) for row in result.result_rows]
    
    def get_categories_summary(self) -> List[Dict[str, Any]]:
        """Получение сводной статистики по категориям"""
        query = """
        SELECT 
            category,
            count(*) as protocols_count,
            sum(tvl) as total_tvl,
            avg(tvl) as avg_tvl,
            max(tvl) as max_tvl
        FROM defi_protocols
        WHERE tvl > 0
        GROUP BY category
        ORDER BY total_tvl DESC
        """
        result = self.execute_query(query)
        return [dict(zip(result.column_names, row)) for row in result.result_rows]
    
    def get_chains_summary(self) -> List[Dict[str, Any]]:
        """Получение сводной статистики по блокчейнам"""
        query = """
        SELECT 
            chain,
            count(*) as protocols_count,
            sum(tvl) as total_tvl,
            avg(tvl) as avg_tvl,
            max(tvl) as max_tvl
        FROM defi_protocols
        WHERE tvl > 0
        GROUP BY chain
        ORDER BY total_tvl DESC
        """
        result = self.execute_query(query)
        return [dict(zip(result.column_names, row)) for row in result.result_rows]
