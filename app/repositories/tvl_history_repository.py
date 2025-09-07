from typing import List, Dict, Any
from datetime import datetime, timedelta
from .filterable_repository import FilterableRepository


class TVLHistoryRepository(FilterableRepository):
    """Репозиторий для работы с историей TVL"""
    
    def __init__(self):
        super().__init__('tvl_history')
    
    def find_by_protocol_id(self, protocol_id: str, days: int = 30, limit: int = 1000) -> List[Dict[str, Any]]:
        """Получение истории TVL для протокола"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query = """
        SELECT * FROM tvl_history
        WHERE protocol_id = %(protocol_id)s
        AND timestamp >= %(start_date)s
        ORDER BY timestamp DESC
        LIMIT %(limit)s
        """
        
        result = self.execute_query(query, {
            'protocol_id': protocol_id,
            'start_date': start_date,
            'limit': limit
        })
        
        return [dict(zip(result.column_names, row)) for row in result.result_rows]
    
    def get_total_tvl_history(self, days: int = 30) -> List[Dict[str, Any]]:
        """Получение истории общего TVL по дням"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query = """
        SELECT 
            toDate(timestamp) as date,
            sum(tvl) as total_tvl,
            count(DISTINCT protocol_id) as protocols_count
        FROM tvl_history
        WHERE timestamp >= %(start_date)s
        GROUP BY toDate(timestamp)
        ORDER BY date DESC
        """
        
        result = self.execute_query(query, {'start_date': start_date})
        return [dict(zip(result.column_names, row)) for row in result.result_rows]
    
    def get_tvl_changes_24h(self) -> List[Dict[str, Any]]:
        """Получение изменений TVL за 24ч для всех протоколов"""
        query = """
        SELECT 
            th.*,
            dp.name,
            dp.category,
            dp.chain
        FROM tvl_history th
        JOIN defi_protocols dp ON th.protocol_id = dp.id
        WHERE th.timestamp >= (now() - INTERVAL 1 DAY)
        AND th.tvl_change_percentage_24h IS NOT NULL
        ORDER BY th.tvl_change_percentage_24h DESC
        """
        
        result = self.execute_query(query)
        return [dict(zip(result.column_names, row)) for row in result.result_rows]
    
    def get_top_tvl_gainers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Получение протоколов с наибольшим ростом TVL за 24ч"""
        query = """
        SELECT 
            dp.name,
            dp.category,
            dp.chain,
            th.tvl,
            th.tvl_change_24h,
            th.tvl_change_percentage_24h
        FROM tvl_history th
        JOIN defi_protocols dp ON th.protocol_id = dp.id
        WHERE th.timestamp >= (now() - INTERVAL 1 DAY)
        AND th.tvl_change_percentage_24h > 0
        ORDER BY th.tvl_change_percentage_24h DESC
        LIMIT %(limit)s
        """
        
        result = self.execute_query(query, {'limit': limit})
        return [dict(zip(result.column_names, row)) for row in result.result_rows]
    
    def get_tvl_summary(self) -> Dict[str, Any]:
        """Получение сводной статистики TVL"""
        query = """
        SELECT 
            sum(tvl) as total_tvl,
            count(DISTINCT protocol_id) as total_protocols,
            avg(tvl) as avg_tvl,
            max(tvl) as max_tvl,
            min(tvl) as min_tvl
        FROM tvl_history
        WHERE timestamp >= (now() - INTERVAL 1 DAY)
        """
        
        result = self.execute_query(query)
        if result.result_rows:
            return dict(zip(result.column_names, result.result_rows[0]))
        return {}