from typing import List, Dict, Any, TypeVar
from .base_repository import BaseRepository

T = TypeVar('T')


class FilterableRepository(BaseRepository[T]):
    """Репозиторий с поддержкой фильтрации"""
    
    def find_with_filters(
        self,
        filters: Dict[str, Any],
        limit: int = 100,
        offset: int = 0,
        order_by: str = 'created_at',
        order_direction: str = 'DESC'
    ) -> List[Dict[str, Any]]:
        """Поиск с фильтрами"""
        conditions = []
        parameters = {'limit': limit, 'offset': offset}
        
        for field, value in filters.items():
            if value is not None:
                condition_key = f"filter_{field}"
                conditions.append(f"{field} = %({condition_key})s")
                parameters[condition_key] = value
        
        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)
        
        query = f"""
        SELECT * FROM {self.table_name}
        {where_clause}
        ORDER BY {order_by} {order_direction}
        LIMIT %(limit)s OFFSET %(offset)s
        """
        
        result = self.execute_query(query, parameters)
        return [dict(zip(result.column_names, row)) for row in result.result_rows]