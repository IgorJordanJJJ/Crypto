from typing import List, Dict, Any, TypeVar
from .base_repository import BaseRepository

T = TypeVar('T')


class SearchableRepository(BaseRepository[T]):
    """Репозиторий с поддержкой поиска"""
    
    def search(
        self, 
        search_term: str, 
        search_fields: List[str],
        limit: int = 100, 
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Поиск по указанным полям"""
        # Создаем условие поиска для каждого поля
        search_conditions = []
        for field in search_fields:
            search_conditions.append(f"{field} ILIKE %(search_term)s")
        
        search_clause = " OR ".join(search_conditions)
        
        query = f"""
        SELECT * FROM {self.table_name}
        WHERE {search_clause}
        ORDER BY created_at DESC
        LIMIT %(limit)s OFFSET %(offset)s
        """
        
        result = self.execute_query(query, {
            'search_term': f'%{search_term}%',
            'limit': limit,
            'offset': offset
        })
        
        return [dict(zip(result.column_names, row)) for row in result.result_rows]